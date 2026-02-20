// Cluster 9

// Node: synchronized
// Node: toJSON
// Node: isOpen
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.enterprise.concurrent.ManagedThreadFactory;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

import com.ibm.websphere.samples.daytrader.web.websocket.JsonDecoder;
import com.ibm.websphere.samples.daytrader.web.websocket.JsonEncoder;
import com.ibm.websphere.samples.daytrader.web.websocket.JsonMessage;

/** This class a simple websocket that sends the number of times it has been pinged. */

@ServerEndpoint(value = "/pingWebSocketJson",encoders=JsonEncoder.class ,decoders=JsonDecoder.class)
public class PingWebSocketJson {

    private Session currentSession = null;
    private Integer sentHitCount = null;
    private Integer receivedHitCount = null;
       
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
        sentHitCount = 0;
        receivedHitCount = 0;
        
        
        InitialContext context;
        ManagedThreadFactory mtf = null;
        
        try {
            context = new InitialContext();
            mtf = (ManagedThreadFactory) context.lookup("java:comp/DefaultManagedThreadFactory");
        
        } catch (NamingException e1) {
            // TODO Auto-generated catch block
            e1.printStackTrace();
        }
        
        Thread thread = mtf.newThread(new Runnable() {

            @Override
            public void run() {
                
                try {
                
                    Thread.sleep(500);
                    
                    while (currentSession.isOpen()) {
                        sentHitCount++;
                    
                        JsonMessage response = new JsonMessage();
                        response.setKey("sentHitCount");
                        response.setValue(sentHitCount.toString());
                        currentSession.getAsyncRemote().sendObject(response);

                        Thread.sleep(100);
                    }
                    
                           
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
                
        });
        
        thread.start();
        
    }

    @OnMessage
    public void ping(JsonMessage message) throws IOException {
        receivedHitCount++;
        JsonMessage response = new JsonMessage();
        response.setKey("receivedHitCount");
        response.setValue(receivedHitCount.toString());
        currentSession.getAsyncRemote().sendObject(response);
    }

    @OnError
    public void onError(Throwable t) {
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {
       
    }

}


// Node: JsonMessage
// Node: setKey
// Node: setValue
// Node: getAsyncRemote
// Node: sendObject
// Node: ping
// Node: StringReader
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

/** This class a simple websocket that sends the number of times it has been pinged. */

@ServerEndpoint(value = "/pingTextAsync")
public class PingWebSocketTextAsync {

    private Session currentSession = null;
    private Integer hitCount = null;
   
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
        hitCount = 0;
    }

    @OnMessage
    public void ping(String text) {

        hitCount++;
        currentSession.getAsyncRemote().sendText(hitCount.toString());
    }

    @OnError
    public void onError(Throwable t) {
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {
     
    }

}


// Node: sendText
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
//import java.util.Collections;
//import java.util.HashSet;
//import java.util.Set;

import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

/** This class a simple websocket that sends the number of times it has been pinged. */

@ServerEndpoint(value = "/pingTextSync")
public class PingWebSocketTextSync {

    private Session currentSession = null;
    private Integer hitCount = null;
   
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
        hitCount = 0;
    }

    @OnMessage
    public void ping(String text) {
        hitCount++;
    
        try {
            currentSession.getBasicRemote().sendText(hitCount.toString());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @OnError
    public void onError(Throwable t) {
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {
               
    }

}


// Node: getBasicRemote
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
import java.nio.ByteBuffer;

import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

/** This class a simple websocket that echos the binary it has been sent. */

@ServerEndpoint(value = "/pingBinary")
public class PingWebSocketBinary {

    private Session currentSession = null;
   
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
    }

    @OnMessage
    public void ping(ByteBuffer data) {       
        currentSession.getAsyncRemote().sendBinary(data);
    }

    @OnError
    public void onError(Throwable t) {
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {

        try {
            if (session.isOpen()) {
                session.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

}


// Node: sendBinary
/**
 * (C) Copyright IBM Corporation 2015, 2025.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.websocket;

import java.io.IOException;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

import javax.annotation.Resource;
import javax.enterprise.concurrent.ManagedScheduledExecutorService;
import javax.enterprise.event.Observes;
import javax.jms.Message;
import javax.json.Json;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;
import javax.json.JsonValue;
import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.WebSocketJMSMessage;


/** This class is a WebSocket EndPoint that sends the Market Summary in JSON form when requested 
 *  and sends stock price changes when received from an MDB through a CDI event
 * */

@ServerEndpoint(value = "/marketsummary",decoders=ActionDecoder.class)
public class MarketSummaryWebSocket {

    @Resource
    private ManagedScheduledExecutorService managedScheduledExecutorService;

	private static final List<Session> SESSIONS = new CopyOnWriteArrayList<>();
    private static final int SCHEDULER_PERIOD = Integer.parseInt(System.getProperty("dt.ws.period", "2"));
    private final CountDownLatch latch = new CountDownLatch(1);

    private static boolean sendRecentQuotePriceChangeList = false;
    private static ScheduledFuture<?> scheduler = null;


    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onOpen -- session -->" + session + "<--");
        }

        synchronized(SESSIONS) {
            if (SESSIONS.size() == 0) {
                 if (Log.doTrace()) {
                    Log.trace("MarketSummaryWebSocket:onOpen -- start scheduler");
                 }
                startScheduler();
            }

            SESSIONS.add(session);
        }
  
        latch.countDown();
    } 
    
    @OnMessage
    public void sendMarketSummary(ActionMessage message, Session currentSession) {

        String action = message.getDecodedAction();
        
        if (Log.doTrace()) {
            if (action != null ) {
                Log.trace("MarketSummaryWebSocket:sendMarketSummary -- received -->" + action + "<--");
            } else {
                Log.trace("MarketSummaryWebSocket:sendMarketSummary -- received -->null<--");
            }
        }

        // Make sure onopen is finished
        try {
            latch.await();
        } catch (InterruptedException e) {
            e.printStackTrace();
            return;
        }
        
        if (action != null && action.equals("update")) {
            TradeAction tAction = new TradeAction();
                            
            JsonObject mkSummary = null;
            try {
                mkSummary = tAction.getMarketSummary().toJSON();
            } catch (Exception e) {
                e.printStackTrace();
                return;
            }

            if (Log.doTrace()) {
                Log.trace("MarketSummaryWebSocket:sendMarketSummary -- sending -->" + mkSummary + "<--");
            }
                            
            if (RecentStockChangeList.isEmpty()) {
                synchronized (currentSession) {
                    if (currentSession.isOpen()) {
                        try {
                            currentSession.getBasicRemote().sendText(mkSummary.toString());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                }   
            }
            else { // Merge Objects 
                JsonObject recentChangeList = RecentStockChangeList.stockChangesInJSON();
                if (currentSession.isOpen()) {
                    try {
                        currentSession.getBasicRemote().sendText(mergeJsonObjects(mkSummary,recentChangeList).toString());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                } 
            }
        }
    }

    @OnError
    public void onError(Throwable t, Session currentSession) {
        if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onError -- session -->" + currentSession + "<--");
        }
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {

        if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onClose -- session -->" + session + "<--");
        }

        synchronized(SESSIONS) {
            SESSIONS.remove(session);
            if (SESSIONS.size() == 0) {  
                if (Log.doTrace()) {
                    Log.trace("MarketSummaryWebSocket:onClose -- cancel scheduler");
                }
                scheduler.cancel(false);
            }
        }

    }
    
    public static void onJMSMessage(@Observes @WebSocketJMSMessage Message message) {
    	
    	if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onJMSMessage");
        }
        RecentStockChangeList.addStockChange(message);
        sendRecentQuotePriceChangeList = true;
    }    

    private void sendRecentQuotePriceChangeList() {
        JsonObject stockChangeJson = RecentStockChangeList.stockChangesInJSON();
  
        for (Session session : SESSIONS) {
            synchronized (session) {
                if (session.isOpen()) {
                    try {
                        session.getBasicRemote().sendText(stockChangeJson.toString());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }      
                }
            }
        }
    }
    

    private void startScheduler() {
		scheduler = managedScheduledExecutorService.scheduleAtFixedRate(() -> {
        Log.trace("MarketSummaryWebSocket: Executing static scheduled task at: " + System.currentTimeMillis());
        if (sendRecentQuotePriceChangeList) {
          Log.trace("MarketSummaryWebSocket: sendList = true");
          sendRecentQuotePriceChangeList();
          sendRecentQuotePriceChangeList = false;
        } else {
          Log.trace("MarketSummaryWebSocket: sendList = false");
        }
      }, 1, SCHEDULER_PERIOD, TimeUnit.SECONDS);
	}
    
    private JsonObject mergeJsonObjects(JsonObject obj1, JsonObject obj2) {
        
        JsonObjectBuilder jObjectBuilder = Json.createObjectBuilder();
        
        Set<String> keys1 = obj1.keySet();
        Iterator<String> iter1 = keys1.iterator();
        
        while(iter1.hasNext()) {
            String key = (String)iter1.next();
            JsonValue value = obj1.get(key);
            
            jObjectBuilder.add(key, value);
            
        }
        
        Set<String> keys2 = obj2.keySet();
        Iterator<String> iter2 = keys2.iterator();
        
        while(iter2.hasNext()) {
            String key = (String)iter2.next();
            JsonValue value = obj2.get(key);
            
            jObjectBuilder.add(key, value);
            
        }
        
        return jObjectBuilder.build();
    }
}



// Node: sendMarketSummary
// Node: getDecodedAction
// Node: await
// Node: isEmpty
// Node: stockChangesInJSON
// Node: mergeJsonObjects
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.websocket;

public class JsonMessage {

    private String key;
    private String value;

    public String getKey() {
      return key;
    }

    public void setKey(String key) {
      this.key = key;
    }

    public String getValue() {
      return value;
    }

    public void setValue(String value) {
      this.value = value;
    }

    
}


/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.websocket;

import java.io.StringReader;

import javax.json.Json;
import javax.json.stream.JsonParser;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *  Licensed to the Apache Software Foundation (ASF) under one or more
 *  contributor license agreements.  See the NOTICE file distributed with
 *  this work for additional information regarding copyright ownership.
 *  The ASF licenses this file to You under the Apache License, Version 2.0
 *  (the "License"); you may not use this file except in compliance with
 *  the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */
public class ActionMessage {
    
    String decodedAction = null;
    
    public ActionMessage() {  
    }
    
    public void doDecoding(String jsonText) {
              
        String keyName = null;
        try 
        {
            // JSON parse
            JsonParser parser = Json.createParser(new StringReader(jsonText));
            while (parser.hasNext()) {
                JsonParser.Event event = parser.next();
                switch(event) {
                case KEY_NAME:
                    keyName=parser.getString();
                    break;
                case VALUE_STRING:
                    if (keyName != null && keyName.equals("action")) {
                        decodedAction=parser.getString();
                    }
                    break;
                default:
                    break;
                }
            }
        } catch (Exception e) {
            Log.error("ActionMessage:doDecoding(" + jsonText + ") --> failed", e);
        }
        
        if (Log.doTrace()) {
            if (decodedAction != null ) {
                Log.trace("ActionMessage:doDecoding -- decoded action -->" + decodedAction + "<--");
            } else {
                Log.trace("ActionMessage:doDecoding -- decoded action -->null<--");
            }
        }
        
    }
    
    public String getDecodedAction() {
        return decodedAction;
    }
    
}



/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.websocket;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

import javax.jms.Message;
import javax.json.Json;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;


/** This class is a holds the last 5 stock changes, used by the MarketSummary WebSocket
 * */

public class RecentStockChangeList {

    private static List<Message> stockChanges = Collections.synchronizedList(new LinkedList<Message>());
       
    public static void addStockChange(Message message) {
        
        stockChanges.add(0, message);
        
        // Add stock, remove if needed
        if(stockChanges.size() > 5) {
            stockChanges.remove(5);
        }
    }
    
    public static JsonObject stockChangesInJSON() {
        
        JsonObjectBuilder jObjectBuilder = Json.createObjectBuilder();
        
        try {
            int i = 1;
            
            List<Message> temp = new LinkedList<Message>(stockChanges);
                        
            for (Iterator<Message> iterator = temp.iterator(); iterator.hasNext();) {
                Message message = iterator.next();
                            
                jObjectBuilder.add("change" + i + "_stock", message.getStringProperty("symbol"));
                jObjectBuilder.add("change" + i + "_price","$" + message.getStringProperty("price"));          
                            
                BigDecimal change = new BigDecimal(message.getStringProperty("price")).subtract(new BigDecimal(message.getStringProperty("oldPrice")));
                change.setScale(2, RoundingMode.HALF_UP);
                
                jObjectBuilder.add("change" + i + "_change", change.toString());
                
                i++;
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        
        return jObjectBuilder.build();
    }
    
    public static boolean isEmpty() {
        return stockChanges.isEmpty();
    }        

}


/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.websocket;

import java.io.StringReader;

import javax.json.Json;
import javax.json.JsonObject;
import javax.websocket.DecodeException;
import javax.websocket.Decoder;
import javax.websocket.EndpointConfig;

public class JsonDecoder implements Decoder.Text<JsonMessage> {

    @Override
    public void destroy() {
    }

    @Override
    public void init(EndpointConfig ec) {
    }

    @Override
    public JsonMessage decode(String json) throws DecodeException {
        JsonObject jsonObject = Json.createReader(new StringReader(json)).readObject();
        
        JsonMessage message = new JsonMessage();
        message.setKey(jsonObject.getString("key"));
        message.setValue(jsonObject.getString("value"));
        
        return message;
    }

    @Override
    public boolean willDecode(String json) {
        try {
            Json.createReader(new StringReader(json)).readObject();
            return true;
          } catch (Exception e) {
            return false;
          }
    }

}


// Node: createReader
// Node: readObject
// Node: willDecode
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.websocket;

import javax.websocket.DecodeException;
import javax.websocket.Decoder;
import javax.websocket.EndpointConfig;

import com.ibm.websphere.samples.daytrader.util.Log;

// This is coded to be a Text type decoder expecting JSON format. 
// It will decode incoming messages into object of type String
public class ActionDecoder implements Decoder.Text<ActionMessage> {

    public ActionDecoder() {
    }
    
    @Override
    public void destroy() {
    }

    @Override
    public void init(EndpointConfig config) {
    }

    @Override
    public ActionMessage decode(String jsonText) throws DecodeException {
       
        if (Log.doTrace()) {
            Log.trace("ActionDecoder:decode -- received -->" + jsonText + "<--");
        }

        ActionMessage actionMessage = new ActionMessage();
        actionMessage.doDecoding(jsonText);
        return actionMessage;

    }

    @Override
    public boolean willDecode(String s) {
        return true;
    }

}


