#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2018 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#


from gevent import monkey; monkey.patch_all()
from azure.storage.queue import QueueService
from base64 import b64decode
import logging
from wishbone.module import InputModule
from wishbone.protocol.decode.plain import Plain


class AzureQueueStorageIn(InputModule):
    '''Consumes messages from Azure Queue Storage

    Consume messages from the Azure Queue Storage service.


    Parameters::

        - account_name(str)("wishbone")
           |  The account name to authenticate to

        - account_key(str)("wishbone")
           |  The account key to authenticate to the queue

        - auto_message_delete(bool)(True)
           |  Once the message is consumed from the queue delete it immediately.

        - b64decode(bool)(True)
           |  Decode the message payload.

        - destination(str)("data")
           |  The location write the payload to

        - endpoint_suffix(str)("core.windows.net")
           |  The endpoint suffix of the service

        - native_events(bool)(False)
           |  Whether to expect incoming events to be native Wishbone events

        - payload(str/dict/int/float)("test")
           |  The content of the test message.

        - queue_name(str)("wishbone")
           |  The name of the queue to consume

        - visibility_timeout(int)(None)
           |  The amount of time the consumed message remains invisible to
           |  other consumers before it gets deleted.

    Queues::

        - outbox
           |  Outgoing events.

        - delete
           |  Events to delete from Queue storage.
    '''

    def __init__(self, actor_config, destination="data", payload=None, native_events=False,
                 account_name="wishbone", account_key="wishbone", queue_name="wishbone", endpoint_suffix='core.windows.net',
                 auto_message_delete=True, visibility_timeout=None, b64decode=True):

        InputModule.__init__(self, actor_config)
        self.pool.createQueue("outbox")
        self.pool.createQueue("delete")

        self.decode = Plain().handler

    def getMessages(self):

        try:
            self.queue_service = QueueService(
                account_name=self.kwargs.account_name,
                account_key=self.kwargs.account_key,
                endpoint_suffix=self.kwargs.endpoint_suffix,
            )
            self.queue_service.create_queue(self.kwargs.queue_name)
        except Exception as err:
            message = "Failed to connect to Azure Queue Service https://%s.queue.%s/%s Reason: " % (self.kwargs.account_name, self.kwargs.endpoint_suffix, self.kwargs.queue_name)
            raise Exception(message + str(err).partition("\n")[0])
        else:
            self.logging.info("Connected to Azure Queue Service https://%s.queue.%s/%s" % (self.kwargs.account_name, self.kwargs.endpoint_suffix, self.kwargs.queue_name))

        while self.loop():
            for message in self.queue_service.get_messages(
                    self.kwargs.queue_name, visibility_timeout=self.kwargs.visibility_timeout):
                for event in self.processIncomingMessage(message):
                    self.submit(event, "outbox")
                if self.kwargs.auto_message_delete:
                    self.queue_service.delete_message(self.kwargs.queue_name, message.id, message.pop_receipt)

    def preHook(self):

        logger = logging.getLogger('azure.storage')
        logger.setLevel(logging.CRITICAL)

        self.sendToBackground(self.getMessages)
        self.sendToBackground(self.processDeleteMessage)

    def processIncomingMessage(self, message):

        if self.kwargs.b64decode:
            data = b64decode(message.content)
        else:
            data = message.content

        for chunk in [data, None]:
            for payload in self.decode(chunk):
                event = self.generateEvent(
                    payload,
                    self.kwargs.destination
                )
                event = self.__setMetaData(event, message)
                yield event

    def processDeleteMessage(self):

        while self.loop():
            event = self.pool.queue.delete.get()
            self.queue_service.delete_message(
                self.kwargs.queue_name,
                event.get('tmp.%s.id' % (self.name)),
                event.get('tmp.%s.pop_receipt' % (self.name))
            )

    def __setMetaData(self, event, message):

        metadata = {
            "id": message.id,
            "insertion_time": message.insertion_time.strftime('%s'),
            "expiration_time": message.expiration_time.strftime('%s'),
            "dequeue_count": message.dequeue_count,
            "pop_receipt": message.pop_receipt,
            "time_next_visible": message.time_next_visible.strftime('%s')
        }
        event.set(metadata, "tmp.%s" % (self.name))
        return event
