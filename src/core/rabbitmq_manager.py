import pika
import json
import time

class RabbitMQManager:
    def __init__(self, host='localhost', queue_name='stock_updates'):
        self.host = host
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=False)
            print(f"✅ Connected to RabbitMQ at {self.host}")
        except Exception as e:
            print(f"❌ RabbitMQ Connection Error: {e}")
            self.connection = None

    def publish(self, message_dict):
        if not self.connection or self.connection.is_closed:
             print("⚠️ RabbitMQ connection lost. Reconnecting...")
             self.connect()
        
        if self.channel:
            try:
                message_body = json.dumps(message_dict)
                self.channel.basic_publish(exchange='',
                                           routing_key=self.queue_name,
                                           body=message_body)
                # print(f"📤 Sent to RabbitMQ: {message_dict.get('Sembol')}")
                return True
            except Exception as e:
                print(f"❌ Failed to publish message: {e}")
                return False
        return False

    def close(self):
        if self.connection:
            self.connection.close()
