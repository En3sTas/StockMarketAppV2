import pika
import json
import time

class RabbitMQManager:
    """
    Manages RabbitMQ connections and message publishing.
    Reads connection settings from config.py (which reads from .env).
    """
    def __init__(self, queue_name='stock_updates'):
        # Import here to avoid circular imports
        from config import RABBITMQ_AYARLARI
        self.host = RABBITMQ_AYARLARI["host"]
        self.port = RABBITMQ_AYARLARI["port"]
        self.user = RABBITMQ_AYARLARI["user"]
        self.password = RABBITMQ_AYARLARI["password"]
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        """
        Establishes a connection to the RabbitMQ server.
        """
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=False)
            print(f"Connected to RabbitMQ at {self.host}:{self.port}")
        except Exception as e:
            print(f"RabbitMQ Connection Error: {e}")
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
                self.channel.basic_publish(exchange='',
                                           routing_key=self.queue_name,
                                           body=message_body)
                return True
            except Exception as e:
                print(f"Failed to publish message: {e}")
                return False
        return False

    def close(self):
        """
        Closes the RabbitMQ connection.
        """
        if self.connection:
            self.connection.close()
