import os

import socketio
from dotenv import load_dotenv

from teai.core.config import load_app_config
from teai.server.config.server_config import load_server_config
from teai.server.conversation_manager.conversation_manager import (
    ConversationManager,
)
from teai.server.monitoring import MonitoringListener
from teai.storage import get_file_store
from teai.storage.conversation.conversation_store import ConversationStore
from teai.storage.settings.settings_store import SettingsStore
from teai.utils.import_utils import get_impl

load_dotenv()

config = load_app_config()
server_config = load_server_config()
file_store = get_file_store(config.file_store, config.file_store_path)

client_manager = None
redis_host = os.environ.get('REDIS_HOST')
if redis_host:
    client_manager = socketio.AsyncRedisManager(
        f'redis://{redis_host}',
        redis_options={'password': os.environ.get('REDIS_PASSWORD')},
    )


sio = socketio.AsyncServer(
    async_mode='asgi', cors_allowed_origins='*', client_manager=client_manager
)

MonitoringListenerImpl = get_impl(
    MonitoringListener,
    server_config.monitoring_listener_class,
)

monitoring_listener = MonitoringListenerImpl.get_instance(config)

ConversationManagerImpl = get_impl(
    ConversationManager,  # type: ignore
    server_config.conversation_manager_class,
)

conversation_manager = ConversationManagerImpl.get_instance(  # type: ignore
    sio, config, file_store, server_config, monitoring_listener
)

SettingsStoreImpl = get_impl(SettingsStore, server_config.settings_store_class)  # type: ignore

ConversationStoreImpl = get_impl(
    ConversationStore,  # type: ignore
    server_config.conversation_store_class,
)
