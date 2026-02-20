// Cluster 106

package net.chrisrichardson.ftgo.common;

import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import io.eventuate.common.json.mapper.JSonMapper;

import javax.annotation.PostConstruct;

public class CommonJsonMapperInitializer {

  @PostConstruct
  public void initialize() {
    registerMoneyModule();
  }

  public static void registerMoneyModule() {
    JSonMapper.objectMapper.registerModule(new MoneyModule());
    JSonMapper.objectMapper.registerModule(new JavaTimeModule());
    JSonMapper.objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

  }
}


// Node: registerModule
// Node: MoneyModule
// Node: JavaTimeModule
// Node: disable
// Node: MoneyDeserializer
package net.chrisrichardson.ftgo.common;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.deser.std.StdScalarDeserializer;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.databind.ser.std.StdScalarSerializer;

import java.io.IOException;

public class MoneyModule extends SimpleModule {

  class MoneyDeserializer extends StdScalarDeserializer<Money> {

    protected MoneyDeserializer() {
      super(Money.class);
    }

    @Override
    public Money deserialize(JsonParser jp, DeserializationContext ctxt) throws IOException, JsonProcessingException {
      JsonToken token = jp.getCurrentToken();
      if (token == JsonToken.VALUE_STRING) {
        String str = jp.getText().trim();
        if (str.isEmpty())
          return null;
        else
          return new Money(str);
      } else
        throw ctxt.mappingException(getValueClass());
    }
  }

  class MoneySerializer extends StdScalarSerializer<Money> {
    public MoneySerializer() {
      super(Money.class);
    }

    @Override
    public void serialize(Money value, JsonGenerator jgen, SerializerProvider provider) throws IOException {
      jgen.writeString(value.asString());
    }
  }

    @Override
  public String getModuleName() {
    return "FtgoCommonMOdule";
  }

  public MoneyModule() {
    addDeserializer(Money.class, new MoneyDeserializer());
    addSerializer(Money.class, new MoneySerializer());
  }

}


// Node: MoneySerializer
// Node: serialize
// Node: writeString
// Node: getModuleName
// Node: addDeserializer
// Node: addSerializer
