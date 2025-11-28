"""
Server-Sent Events (SSE) route
Provides real-time event stream to clients
"""
from flask import current_app, Response
from routes import sse_bp
import queue
import logging

logger = logging.getLogger(__name__)


@sse_bp.route('/events', methods=['GET'])
def stream_events():
    """
    SSE event stream endpoint

    Returns:
        SSE stream response
    """
    sse_broadcaster = current_app.config['SSE_BROADCASTER']

    # Add this client to broadcaster
    client_queue = sse_broadcaster.add_client()

    def event_stream():
        """Generate SSE events"""
        try:
            while True:
                try:
                    # Get message from queue (30s timeout for keepalive)
                    message = client_queue.get(timeout=30)

                    # Format as SSE
                    import json
                    yield f"data: {json.dumps(message)}\n\n"

                except queue.Empty:
                    # Send keepalive comment to prevent timeout
                    yield ": keepalive\n\n"

        except (GeneratorExit, Exception) as e:
            # Client disconnected or error occurred
            logger.debug(f"SSE client disconnected: {e}")
        finally:
            # Always cleanup
            sse_broadcaster.remove_client(client_queue)

    response = Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Connection': 'keep-alive',
        }
    )

    # Cleanup on response close
    @response.call_on_close
    def on_close():
        sse_broadcaster.remove_client(client_queue)

    return response
