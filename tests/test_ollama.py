"""Kiểm tra adapter local không cần key và các lỗi của agent, không gọi mạng."""
import json
import os
import unittest
from unittest.mock import patch

from agent import run_agent
from providers import CONFIG, Provider
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class OllamaProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    @patch('providers.post_json')
    def test_no_api_key_and_no_authorization_for_agent_and_judge(self, post):
        tool_message = tool_call('local-1', 'get_status', '{"provider":"github"}')['message']
        post.side_effect = [
            {'choices': [{'message': tool_message, 'finish_reason': 'tool_calls'}]},
            {'choices': [{'message': {'role': 'assistant', 'content': '{}', 'tool_calls': None}, 'finish_reason': 'stop'}]},
        ]
        client = Provider('ollama', 'qwen3.5:4b')
        result = client.complete([{'role': 'user', 'content': 'Kiểm tra GitHub'}], [{'tool': 'schema'}])
        self.assertEqual(result['calls'][0]['id'], 'local-1')
        self.assertIs(result['message'], tool_message)
        client.complete([{'role': 'user', 'content': 'Chấm JSON'}], [])
        for request in post.call_args_list:
            url, headers, payload = request.args
            self.assertEqual(url, 'http://127.0.0.1:11434/v1/chat/completions')
            self.assertEqual(headers, {})
            self.assertEqual(payload['model'], 'qwen3.5:4b')
            self.assertEqual(payload['reasoning_effort'], 'none')
            self.assertEqual(request.kwargs['timeout'], 180)
        self.assertIn('tools', post.call_args_list[0].args[2])
        self.assertNotIn('tools', post.call_args_list[1].args[2])

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'unused', 'OLLAMA_API_KEY': 'unused'}, clear=True)
    @patch('providers.post_json')
    def test_existing_keys_are_not_sent_to_ollama(self, post):
        post.return_value = {'choices': [{'message': {'role': 'assistant', 'content': 'ok'}, 'finish_reason': 'stop'}]}
        Provider('ollama', 'local').complete([], [])
        self.assertEqual(post.call_args.args[1], {})

    @patch.dict(os.environ, {}, clear=True)
    def test_cloud_providers_still_require_their_keys(self):
        for name, (key_name, _) in CONFIG.items():
            if key_name:
                with self.subTest(provider=name), self.assertRaisesRegex(ValueError, key_name):
                    Provider(name, 'test')


class AgentErrorTests(unittest.TestCase):
    def test_non_object_arguments_return_observation(self):
        for arguments in ('[]', 'null', '42'):
            with self.subTest(arguments=arguments):
                provider = FakeProvider([tool_call('bad', 'get_status', arguments), final()])
                self.assertEqual(run_agent('x', provider, StatusTools())['status'], 'completed')
                observation = json.loads(provider.histories[1][-1]['content'])
                self.assertEqual(observation['error'], 'INVALID_ARGUMENTS')

    def test_provider_failure_is_traced_and_not_completed(self):
        with patch.object(Provider, 'complete', side_effect=RuntimeError('Ollama offline')):
            result = run_agent('x', Provider('ollama', 'local'), StatusTools())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['trace'][-1]['event'], 'error')
        self.assertEqual(result['usage'], [])

    def test_unexpected_stop_reason_is_not_completed(self):
        reply = final('partial')
        reply['finish'] = 'content_filter'
        self.assertEqual(run_agent('x', FakeProvider([reply]), StatusTools())['status'], 'error')

    def test_tool_exception_is_returned_with_call_id(self):
        tools = StatusTools()
        provider = FakeProvider([tool_call('timeout', 'get_status', '{}'), final('Không đủ dữ liệu')])
        with patch.object(tools, 'execute', side_effect=TimeoutError('timeout')):
            result = run_agent('x', provider, tools)
        self.assertEqual(result['status'], 'completed')
        message = provider.histories[1][-1]
        self.assertEqual(message['tool_call_id'], 'timeout')
        self.assertEqual(json.loads(message['content'])['error'], 'TimeoutError')

    def test_persistent_rate_limit_stops_network_retries(self):
        responses = [tool_call(str(i), 'get_status', '{"provider":"github"}') for i in range(3)]
        provider = FakeProvider(responses + [final('Không kiểm tra được do 429')])
        tools = StatusTools()
        with patch.object(tools, 'execute', return_value={
            'ok': False, 'error': 'RATE_LIMITED', 'retry_after_seconds': 0,
        }) as execute:
            result = run_agent('x', provider, tools)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(json.loads(provider.histories[3][-1]['content'])['error'], 'RETRY_LIMIT_REACHED')

    def test_long_retry_after_is_respected_without_blocking(self):
        provider = FakeProvider([tool_call('1', 'get_status', '{}'),
                                 tool_call('2', 'get_status', '{}'), final('Chưa kiểm tra được')])
        tools = StatusTools()
        with patch.object(tools, 'execute', return_value={
            'ok': False, 'error': 'RATE_LIMITED', 'retry_after': '120',
        }) as execute, patch('agent.time.sleep') as sleep:
            result = run_agent('x', provider, tools)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(execute.call_count, 1)
        sleep.assert_not_called()
        self.assertEqual(json.loads(provider.histories[2][-1]['content'])['error'], 'RETRY_DEFERRED')


if __name__ == '__main__':
    unittest.main()
