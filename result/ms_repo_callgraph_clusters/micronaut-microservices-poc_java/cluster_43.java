// Cluster 43

package pl.altkom.asc.lab.micronaut.poc.chat.service.infrastructure.adapters.web;

import io.micronaut.websocket.WebSocketBroadcaster;
import io.micronaut.websocket.WebSocketSession;
import io.micronaut.websocket.annotation.OnClose;
import io.micronaut.websocket.annotation.OnMessage;
import io.micronaut.websocket.annotation.OnOpen;
import io.micronaut.websocket.annotation.ServerWebSocket;
import lombok.extern.slf4j.Slf4j;

import java.util.function.Predicate;

@Slf4j
@ServerWebSocket("/ws/chat/{topic}/{username}")
public class ChatWebSocket {

    private WebSocketBroadcaster broadcaster;

    public ChatWebSocket(WebSocketBroadcaster broadcaster) {
        this.broadcaster = broadcaster;
    }

    @OnOpen
    public void onOpen(String topic, String username, WebSocketSession session) {
        String msg = "[" + username + "] Joined!";
        log.info(msg);
        broadcaster.broadcastSync(formatStartCloseMessages(msg), isValid(topic, session));
    }

    @OnMessage
    public void onMessage(
            String topic,
            String username,
            String message,
            WebSocketSession session) {
        String msg = "[" + username + "] " + message;
        log.info(msg);
        broadcaster.broadcastSync(message, isValid(topic, session));
    }

    @OnClose
    public void onClose(
            String topic,
            String username,
            WebSocketSession session) {
        String msg = "[" + username + "] Disconnected!";
        log.info(msg);
        broadcaster.broadcastSync(formatStartCloseMessages(msg), isValid(topic, session));
    }

    private Predicate<WebSocketSession> isValid(String topic, WebSocketSession session) {
        return s -> s != session && topic.equalsIgnoreCase(s.getUriVariables().get("topic", String.class, null));
    }

    private String formatStartCloseMessages(String msg) {
        return "<p>" + msg + "</p>";
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/chat-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/chat/service/infrastructure/adapters/web/ChatWebSocket.java:ChatWebSocket.<init>
// Node: ServerWebSocket
// Node: ChatWebSocket
