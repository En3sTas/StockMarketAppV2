import pika
import json
import time


class RabbitMQManager:
    """
    Manages RabbitMQ connections and message publishing.
    Reads connection settings from config.py (which reads from .env).
    """
    def __init__(self, queue_name='stock_updates'):
        from config import RABBITMQ_CONFIG
        self.host       = RABBITMQ_CONFIG["host"]
        self.port       = RABBITMQ_CONFIG["port"]
        self.user       = RABBITMQ_CONFIG["user"]
        self.password   = RABBITMQ_CONFIG["password"]
        self.queue_name = queue_name
        self.connection = None
        self.channel    = None
        self.connect()

    def connect(self):
        """Establishes a connection to the RabbitMQ server."""
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(params)
            self.channel    = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=False)
            print(f"Connected to RabbitMQ at {self.host}:{self.port}")
        except Exception as e:
            print(f"RabbitMQ connection error: {e}")
            self.connection = None

    def publish(self, message_dict):
        """
        Publishes a message to the defined queue.
        Reconnects if the connection is lost.
        """
        if not self.connection or self.connection.is_closed:
            print("RabbitMQ connection lost. Reconnecting...")
            self.connect()

        if self.channel:
            try:
                message_body = json.dumps(message_dict)
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue_name,
                    body=message_body
                )
                return True
            except Exception as e:
                print(f"Failed to publish message: {e}")
                return False
        return False

    def close(self):
        """Closes the RabbitMQ connection."""
        if self.connection:
            self.connection.close()
