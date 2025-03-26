import os

from teai.core.logger import teai_logger as logger
from teai.server.types import AppMode, ServerConfigInterface
from teai.utils.import_utils import get_impl


class ServerConfig(ServerConfigInterface):
    config_cls = os.environ.get('TEAI_CONFIG_CLS', None)
    app_mode = AppMode.OSS
    posthog_client_key = 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    github_client_id = os.environ.get('GITHUB_APP_CLIENT_ID', '')
    enable_billing = os.environ.get('ENABLE_BILLING', 'false') == 'true'
    hide_llm_settings = os.environ.get('HIDE_LLM_SETTINGS', 'false') == 'true'
    settings_store_class: str = (
        'teai.storage.settings.file_settings_store.FileSettingsStore'
    )
    conversation_store_class: str = (
        'teai.storage.conversation.file_conversation_store.FileConversationStore'
    )
    conversation_manager_class: str = 'teai.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager'
    monitoring_listener_class: str = 'teai.server.monitoring.MonitoringListener'

    def verify_config(self):
        if self.config_cls:
            raise ValueError('Unexpected config path provided')

    def get_config(self):
        config = {
            'APP_MODE': self.app_mode,
            'GITHUB_CLIENT_ID': self.github_client_id,
            'POSTHOG_CLIENT_KEY': self.posthog_client_key,
            'FEATURE_FLAGS': {
                'ENABLE_BILLING': self.enable_billing,
                'HIDE_LLM_SETTINGS': self.hide_llm_settings,
            },
        }

        return config


def load_server_config():
    config_cls = os.environ.get('TEAI_CONFIG_CLS', None)
    logger.info(f'Using config class {config_cls}')

    server_config_cls = get_impl(ServerConfig, config_cls)
    server_config = server_config_cls()
    server_config.verify_config()

    return server_config
