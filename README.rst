::

              __       __    __
    .--.--.--|__.-----|  |--|  |--.-----.-----.-----.
    |  |  |  |  |__ --|     |  _  |  _  |     |  -__|
    |________|__|_____|__|__|_____|_____|__|__|_____|


    =================================================
    wishbone_contrib.module.input.azure-queue-storage
    =================================================

    Version: 1.0.0

    Consumes messages from Azure Queue Storage
    ------------------------------------------

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

