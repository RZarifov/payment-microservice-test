from faststream.rabbit import RabbitBroker

from app.settings.config import settings

broker = RabbitBroker(settings.rabbitmq_url)
