// Cluster 20

package com.itachallenge.userinteraction.document;

import lombok.*;
import lombok.experimental.SuperBuilder;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
@ToString
@AllArgsConstructor
public abstract class InteractionDocument {

    @Id
    @Field("_id")
    @EqualsAndHashCode.Include
    private UUID uuid;

    @Field("userId")
    @Indexed
    private UUID userId;

    @Field("challengeId")
    @Indexed
    private UUID challengeId;

    @CreatedDate
    @Field(name = "createdAt")
    private LocalDateTime createdAt;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/document/InteractionDocument.java:InteractionDocument.<init>
// Node: EqualsAndHashCode
// Node: Field
package com.itachallenge.userinteraction.document.bookmark;

import com.itachallenge.userinteraction.document.InteractionDocument;
import lombok.*;
import lombok.experimental.SuperBuilder;
import org.springframework.data.mongodb.core.mapping.Document;

@Getter
@Setter
@SuperBuilder
@NoArgsConstructor
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Document(collection="bookmarks")
public class BookmarkDocument extends InteractionDocument {}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/document/bookmark/BookmarkDocument.java:BookmarkDocument.<init>
// Node: ToString
// Node: Document
package com.itachallenge.userinteraction.document.favorite;


import com.itachallenge.userinteraction.document.InteractionDocument;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.EqualsAndHashCode;
import lombok.experimental.SuperBuilder;
import org.springframework.data.mongodb.core.mapping.Document;
import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Setter
@SuperBuilder
@NoArgsConstructor
@EqualsAndHashCode(callSuper = true)
@Document(collection="favorites")
public class FavoriteDocument extends InteractionDocument {}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/userinteraction/document/favorite/FavoriteDocument.java:FavoriteDocument.<init>
package com.itachallenge.user.document;

import com.itachallenge.user.document.enums.Role;
import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import org.springframework.data.mongodb.core.index.Indexed;

import java.util.*;
import java.util.stream.Collectors;

@AllArgsConstructor
@Data
@Builder
@NoArgsConstructor
@Document(collection="users")
public class UserDocument {

    @Id
    @Field("_id")
    private UUID uuid;

    @Field("username")
    @Indexed(unique = true)
    private String username;

    @Field("role")
    private Role role;

    @Builder.Default
    @Field
    private Integer points = 0;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/document/UserDocument.java:UserDocument.<init>
// Node: Indexed
package com.itachallenge.user.document;

import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.UUID;

@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
@Builder
public class SolutionAttemptDocument {

    @Id
    @Field(name="id_solution")
    private UUID uuid;

    @Field(name="solution_text")
    private String solutionText;

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/document/SolutionAttemptDocument.java:SolutionAttemptDocument.<init>
package com.itachallenge.user.document;

import com.itachallenge.user.document.enums.ChallengeStatus;
import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.List;
import java.util.UUID;
@AllArgsConstructor
@Getter
@Setter
@Builder
@NoArgsConstructor
@Document(collection="solutions")
public class UserSolutionDocument {

    @Id
    @Field("_id")
    private UUID uuid;

    @Field("user_id")
    private UUID userId;

    @Field("challenge_id")
    private UUID challengeId;

    @Field("language_id")
    private UUID languageId;

    @Field("status")
    private ChallengeStatus status;

    @Field("solution")
    private SolutionAttemptDocument solutionAttemptDocument;

}




// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/document/UserSolutionDocument.java:UserSolutionDocument.<init>
// Node: exists
package com.itachallenge.submission.document;

import com.itachallenge.submission.enums.SubmissionStatus;
import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.UUID;

@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
@Builder
@Document(collection = "submissions")
public class SubmissionDocument {

    @Id
    @Field("_id")
    private UUID submissionId;

    @Field("user_id")
    private UUID userId;

    @Field("challenge_id")
    private UUID challengeId;

    @Field("language_id")
    private UUID languageId;

    @Field("status")
    private SubmissionStatus status;

    @Field("submission")
    private String submissionText;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/submission/document/SubmissionDocument.java:SubmissionDocument.<init>
// Node: Query
package com.itachallenge.challenge.document;

import com.itachallenge.challenge.enums.Topic;
import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.LocalDateTime;
import java.util.*;

@Document(collection="challenges")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChallengeDocument {

    @Id
    @Field("_id")
    private UUID uuid;

    @Field(name = "challenge_title")
    private String title;

    @Field(name = "level")
    private String level;   //valor seteado fom properties

    @Field(name = "creation_date")
    private LocalDateTime creationDate;

    @Field(name = "detail")
    private DetailDocument detail;

    @Field(name = "languages")
    private Set<LanguageDocument> languages;

    @Field(name = "solutions")
    private List<UUID> solutions;

    @Field(name = "topic")
    private Topic topic;

    @Field(name = "times_favorite")
    private Integer timesFavorite;

    @Field(name="times_bookmark")
    private Integer timesBookmark;

    @Field(name="times_solved")
    private Integer timesSolved;

    @Field(name = "tags")
    private List<UUID> tags;

    public void increaseTimesFavorite () {
            timesFavorite = timesFavorite == null ? 1 : timesFavorite + 1;
        }

        public void decreaseTimesFavorite () {
            timesFavorite = Integer.max(timesFavorite == null ? 0 : timesFavorite - 1, 0);

        }

    public void increaseTimesBookmark() {
        timesBookmark = timesBookmark == null ? 1 : timesBookmark + 1;
    }

    public void decreaseTimesBookmark() {
        timesBookmark =Integer.max(timesBookmark == null ? 0 : timesBookmark - 1, 0);
    }
  
    public void increaseTimesSolved() {
        timesSolved = timesSolved == null ? 1 : timesSolved + 1;
    }


}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/document/ChallengeDocument.java:ChallengeDocument.<init>
package com.itachallenge.challenge.document;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.UUID;

@Document(collection="tags")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class TagDocument {

    @Id
    @Field(name="id_")
    private UUID idTag;

    @Field(name="tag_name")
    private String tagName;

    @Field(name="tag_description")
    private String tagDescription;

    @Field(name = "language_id")
    private UUID languageId;

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/document/TagDocument.java:TagDocument.<init>
package com.itachallenge.challenge.document;

import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.UUID;

@Document(collection="solutions")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SolutionDocument {

    @Id
    @Field(name="id_solution")
    private UUID uuid;

    @Field(name="solution_text")
    private String solutionText;

    @Field(name="language")
    private UUID idLanguage;
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/document/SolutionDocument.java:SolutionDocument.<init>
package com.itachallenge.challenge.document;

import lombok.*;
import org.springframework.data.mongodb.core.mapping.Field;

@Getter
@AllArgsConstructor
@NoArgsConstructor
public class DetailDocument {

    @Field(name="description")
    private String description;

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/document/DetailDocument.java:DetailDocument.<init>
package com.itachallenge.challenge.document;

import com.itachallenge.challenge.enums.AssociationType;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import java.util.List;
import java.util.UUID;

@Document(collection = "resources")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ResourceDocument {

    @Id
    @Field("_id")
    private UUID resourceId;

    @Field(name = "title")
    private String title;

    @Field(name = "description")
    private String description;

    @Field(name = "url")
    private String url;

    @Field(name = "topic")
    private Topic topic;

    @Field(name = "content_type")
    private ResourceContentType contentType;

    @Field(name = "challenge_ids")
    private List<UUID> challengeIds;

    @Field(name = "association_type")
    private AssociationType associationType;

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/document/ResourceDocument.java:ResourceDocument.<init>
package com.itachallenge.challenge.document;

import lombok.*;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import java.util.UUID;

@Document(collection="languages")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class LanguageDocument {

    @Id
    @Field(name="id_languages")
    private UUID idLanguage;

    @Field(name="language_name")
    private String languageName;

    @Field(name="language_image")
    private String languageImage;

    public String getLanguageImage() {
        return (languageImage != null) ? languageImage : "https://default-image.com/default.png";
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/document/LanguageDocument.java:LanguageDocument.<init>
package com.itachallenge.challenge.config.dbchangelog;

import com.itachallenge.challenge.document.LanguageDocument;
import com.mongodb.reactivestreams.client.MongoDatabase;
import io.mongock.api.annotations.*;
import io.mongock.driver.mongodb.reactive.util.MongoSubscriberSync;
import io.mongock.driver.mongodb.reactive.util.SubscriberSync;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Component;

import java.util.UUID;

import static org.springframework.data.mongodb.core.query.Criteria.where;

@Component
@ChangeUnit(id = "DatabaseInitalizerDemo", order = "1", author = "Ernesto Arcos / Pedro López")
public class DatabaseInitializer {

    Query query = new Query(where("_id").ne(null));
    private final Logger logger = LoggerFactory.getLogger(DatabaseInitializer.class);
    private static final String COLLECTION_NAME = "mongockDemo";

    // Method to create a new collection before the execution of the change unit
    @BeforeExecution
    public void createCollection(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.createCollection(COLLECTION_NAME).subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockDemo collection created");
    }

    // Method to rollback the changes before the execution of the change unit, in case of any failure
    @RollbackBeforeExecution
    public void rollbackBeforeExecution(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.getCollection(COLLECTION_NAME).drop().subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockDemo collection droped");
    }

    // Method to execute the changes in the database
    @Execution
    public void execution(ReactiveMongoTemplate reactiveMongoTemplate) {
        LanguageDocument languageDocument = new LanguageDocument(UUID.randomUUID(), "JAVA", null);
        reactiveMongoTemplate.save(languageDocument, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nexecution"))
                .subscribe();
    }

    // Method to rollback the changes in case of any failure during the execution
    @RollbackExecution
    public void rollback(ReactiveMongoTemplate reactiveMongoTemplate) {
        reactiveMongoTemplate.remove(query, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nrollback"))
                .then();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/config/dbchangelog/DatabaseInitializer.java:DatabaseInitializer.<init>
// Node: ChangeUnit
// Node: where
// Node: ne
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.client.result.UpdateResult;
import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoCollection;
import io.mongock.api.annotations.ChangeUnit;
import io.mongock.api.annotations.Execution;
import io.mongock.api.annotations.RollbackExecution;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import reactor.core.publisher.Mono;

import static org.springframework.data.mongodb.core.query.Criteria.where;
import static org.springframework.data.mongodb.core.query.Query.query;
import static org.springframework.data.mongodb.core.query.Update.update;


/*
 * This class is a change log that updates the database by adding a new field to all documents in a collection,
 * then updates the field name in all documents in the collection, and modifies text in the field.
 * The class uses the reactive MongoDB driver to interact with the database.
 * The class is annotated with @ChangeUnit, which specifies the id, order, and author of the change log.
 * The class do an intentional rollback of the changes made in the execution method to demonstrate the rollback feature.
 * If you want to do a new Order, you can do a new class with the same structure and change the order in the annotation.
 *
 * Author: Dani Diaz
 */

@ChangeUnit(id="DatabaseUpdaterDemo", order = "2", author = "Daniel Diaz")
public class DatabaseUpdater {
    private static final Logger logger = LoggerFactory.getLogger(DatabaseUpdater.class);
    private final ReactiveMongoTemplate reactiveMongoTemplate;

    private static final String DATABASE_NAME = "challenges";
    private static final String COLLECTION_NAME = "mongockDemo";
    private static final String FIELD_NAME = "language_name";
    private static final String NEW_FIELD_NAME = "Language Name Updated";
    private static final String STATE_FIELD = "State";
    private static final String ERROR_UPDATE = "Error during update: {}";
    private static final String EXIST = "$exists";
    // Constructor to initialize the ReactiveMongoTemplate
    public DatabaseUpdater(ReactiveMongoTemplate reactiveMongoTemplate) {
        this.reactiveMongoTemplate = reactiveMongoTemplate;
    }

    // Execution method that is called to perform the database update operations
    @Execution
    public void execution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution started");

        addFieldToAllDocuments(reactiveMongoTemplate);
        logger.info("Field added to all documents");

        updateFieldInCollection(client);
        logger.info("Field updated in collection");
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution completed successfully");
    }

    // Rollback method that is called to revert the database update operations in case of any failure
    @RollbackExecution
    public void rollBackExecution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution started");
        rollbackUpdateFieldInCollection(client);
        logger.info("Field updated in collection rolled back");

        removeFieldToAllDocuments(reactiveMongoTemplate);
        logger.info("Field removed from all documents");
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution completed successfully");

    }

    // Method to update a field in a collection
    public void updateFieldInCollection(MongoClient client){
        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Mono.from(collection.updateMany(
                        new Document(FIELD_NAME, new Document(EXIST, true)),
                        new Document("$rename", new Document(FIELD_NAME, NEW_FIELD_NAME))
                )).doOnSuccess(updateResult ->
                        logger.info("Field '{}' renamed to '{}'", FIELD_NAME, NEW_FIELD_NAME))
                .doOnError(error ->
                        logger.error(ERROR_UPDATE, error.getMessage()))
                .subscribe();
    }
    // Method to roll back the update operation performed on a field in a collection
    public void rollbackUpdateFieldInCollection(MongoClient client){
        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Mono.from(collection.updateMany(
                        new Document(NEW_FIELD_NAME, new Document(EXIST, true)),
                        new Document("$rename", new Document(NEW_FIELD_NAME, FIELD_NAME))
                )).doOnSuccess(updateResult ->
                        logger.info("Field '{}' renamed back to '{}'", NEW_FIELD_NAME, FIELD_NAME))
                .doOnError(error ->
                        logger.error("Error during rollback: {}", error.getMessage()))
                .subscribe();
    }


    // Method to add a new field to all documents in a collection
    public void addFieldToAllDocuments(ReactiveMongoTemplate reactiveMongoTemplate) {
        reactiveMongoTemplate.updateMulti(
                query(where(FIELD_NAME).exists(true)), // Query to match all documents with the FIELD_NAME
                update(STATE_FIELD, "ACTIVE"),
                COLLECTION_NAME
        ).doOnSuccess(result -> {
            logger.info("Matched count: {}", result.getMatchedCount());
            logger.info("Modified count: {}", result.getModifiedCount());
        }).doOnError(error -> logger.error(ERROR_UPDATE, error.getMessage())).subscribe();
    }

    // Method to remove a field from all documents in a collection
    public void removeFieldToAllDocuments(ReactiveMongoTemplate reactiveMongoTemplate) {
        Query query = Query.query(where(FIELD_NAME).exists(true));
        reactiveMongoTemplate.updateMulti(query, new Update().unset(STATE_FIELD), COLLECTION_NAME)
                .defaultIfEmpty(UpdateResult.unacknowledged())
                .doOnSuccess(result -> {
                    logger.info("Matched count: {}", result.getMatchedCount());
                    logger.info("Modified count: {}", result.getModifiedCount());
                })
                .doOnError(error -> logger.error(ERROR_UPDATE, error.getMessage()))
                .subscribe();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/config/dbchangelog/DatabaseUpdater.java:is.<init>
// Node: addFieldToAllDocuments
// Node: updateFieldInCollection
// Node: rollBackExecution
// Node: rollbackUpdateFieldInCollection
// Node: removeFieldToAllDocuments
// Node: updateMulti
// Node: query
// Node: update
// Node: getMatchedCount
// Node: getModifiedCount
// Node: Update
// Node: unset
// Node: unacknowledged
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoCollection;
import io.mongock.api.annotations.ChangeUnit;
import io.mongock.api.annotations.Execution;
import io.mongock.api.annotations.RollbackExecution;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import static com.mongodb.client.model.Updates.rename;

/*
 * This class is a change log that updates the database by adding a new field to all documents in a collection,
 * then updates the field name in all documents in the collection.
 * The class uses the reactive MongoDB driver to interact with the database.
 * The class is annotated with @ChangeUnit, which specifies the id, order, and author of the change log.
 * The class do an intentional rollback of the changes made in the execution method to demonstrate the rollback feature.
 * If you want to do a new Order, you can do a new class with the same structure and change the order in the annotation.
 *
 * @Author: Dani Diaz
 */

@Component
@ChangeUnit(id = "Intentional Rollback order", order = "5", author = "Daniel Diaz")
public class DataBaseRollback {

    private static final Logger logger = LoggerFactory.getLogger(DataBaseRollback.class);

    private static final String DATABASE_NAME = "challenges";
    private static final String COLLECTION_NAME = "mongockDemo";
    private static final String FIELD_NAME_UPDATED = "Language Rollbacked";
    private static final String FIELD_NAME = "Language Name Updated";


    @Execution
    public void execution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution started");

            updateFieldInCollection(client);
            logger.info("Field updated in collection");
    }

    @RollbackExecution
    public void rollBackExecution(MongoClient client) {
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution started");

        rollbackUpdateFieldInCollection(client);
        updateTextInField(client);
        logger.info("Field updated in collection rolled back");
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution completed successfully");

    }

    public void updateFieldInCollection(MongoClient client) {

        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Document updateQuery = new Document("invalidOperator", new Document("$invalid", "someValue"));

        Mono.from(collection.updateMany(
                        new Document(FIELD_NAME_UPDATED, new Document("$exists", true)),
                        updateQuery))
                .doOnSuccess(updateResult -> logger.info("Field '{}' renamed to '{}'", FIELD_NAME, FIELD_NAME_UPDATED))
                .doOnError(error -> logger.error("Update failed: {}", error.getMessage()))
                .block();
    }


    public void updateTextInField(MongoClient client) {
        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);

        Document filter = new Document(FIELD_NAME_UPDATED, "LanguageDemo");
        Document update = new Document("$set", new Document(FIELD_NAME_UPDATED, "LanguageUpdated"));

        Mono.from(collection.updateMany(filter, update))
                .doOnSuccess(updateResult -> logger.info("Field '{}' updated from 'LanguageDemo' to 'LanguageUpdateD'", FIELD_NAME_UPDATED))
                .block();
    }



    public void rollbackUpdateFieldInCollection(MongoClient client) {

        MongoCollection<Document> collection = client.getDatabase(DATABASE_NAME).getCollection(COLLECTION_NAME);
        Mono.from(collection.updateMany(
                        new Document(FIELD_NAME, new Document("$exists", true)),
                        rename(FIELD_NAME, FIELD_NAME_UPDATED)))
                .doOnSuccess(updateResult -> logger.info("Field '{}' renamed back to '{}'", FIELD_NAME, FIELD_NAME_UPDATED))
                .block();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/config/dbchangelog/DataBaseRollback.java:is.<init>
// Node: updateTextInField
// Node: set
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.client.result.UpdateResult;
import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoCollection;
import com.mongodb.reactivestreams.client.MongoDatabase;
import org.bson.Document;
import org.bson.conversions.Bson;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.reactivestreams.Publisher;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import reactor.core.publisher.Mono;

import static org.mockito.Mockito.*;
import static org.springframework.data.mongodb.core.query.Criteria.where;
import static reactor.core.publisher.Mono.empty;
import static reactor.core.publisher.Mono.just;

class DatabaseUpdaterUnitTest {

    private static final String COLLECTION_NAME = "mongockDemo";
    private static final String FIELD_NAME = "language_name";
    private static final String NEW_FIELD_NAME = "Language Name Updated";
    private static final String STATE_FIELD = "State";
    @Mock
    private MongoDatabase mongoDatabase;

    @Mock
    private ReactiveMongoTemplate reactiveMongoTemplate;
    @Mock
    MongoClient mongoClient;

    @InjectMocks
    private DatabaseUpdater databaseUpdater;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @DisplayName("Test execution method - in DatabaseUpdater")
    @Test
    void executionTest() {

        ReactiveMongoTemplate reactiveMongoTemplateMock = mock(ReactiveMongoTemplate.class);
        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);


        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = Mono.just(updateResult);

        // Configurar mocks para MongoClient y MongoDatabase
        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection(COLLECTION_NAME)).thenReturn(mongoCollection);
        when(mongoCollection.updateMany(any(Bson.class), any(Bson.class))).thenReturn(updateResultPublisher);
        when(reactiveMongoTemplateMock.updateMulti(any(), any(), eq(COLLECTION_NAME))).thenReturn(empty());

        DatabaseUpdater databaseUpdater = new DatabaseUpdater(reactiveMongoTemplateMock);
        databaseUpdater.execution(mongoClient);

        verify(mongoCollection).updateMany(any(Bson.class), any(Bson.class));
        verify(reactiveMongoTemplateMock, times(1)).updateMulti(any(Query.class), any(Update.class), eq(COLLECTION_NAME));
    }

    @DisplayName("Test rollBackExecution method - in DatabaseUpdater")
    @Test
    void rollBackExecutionTest() {

        ReactiveMongoTemplate reactiveMongoTemplateMock = mock(ReactiveMongoTemplate.class);
        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);


        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = just(updateResult);

        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection("mongockDemo")).thenReturn(mongoCollection);
        when(mongoCollection.updateMany((Bson) any(), (Bson) any())).thenReturn(updateResultPublisher);
        when(reactiveMongoTemplateMock.updateMulti(any(), any(), eq("mongockDemo"))).thenReturn(empty());

        DatabaseUpdater databaseUpdater = new DatabaseUpdater(reactiveMongoTemplateMock);
        databaseUpdater.rollBackExecution(mongoClient);

        verify(mongoCollection).updateMany((Bson) any(), (Bson) any());

    }

    @Test
    void updateFieldInCollectionTest() {

        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);
        Bson filter = new Document(FIELD_NAME, new Document("$exists", true));
        Bson update = new Document("$rename", new Document(FIELD_NAME, NEW_FIELD_NAME));
        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = Mono.just(updateResult);

        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection(COLLECTION_NAME)).thenReturn(mongoCollection);
        when(mongoCollection.updateMany(filter, update)).thenReturn(updateResultPublisher);

        databaseUpdater.updateFieldInCollection(mongoClient);

        verify(mongoCollection).updateMany(filter, update);
    }

    @Test
    void rollbackUpdateFieldInCollectionTest() {

        MongoCollection<Document> mongoCollection = mock(MongoCollection.class);
        Bson filter = new Document(NEW_FIELD_NAME, new Document("$exists", true));
        Bson update = new Document("$rename", new Document(NEW_FIELD_NAME, FIELD_NAME));
        UpdateResult updateResult = mock(UpdateResult.class);
        Publisher<UpdateResult> updateResultPublisher = Mono.just(updateResult);

        when(mongoClient.getDatabase("challenges")).thenReturn(mongoDatabase);
        when(mongoDatabase.getCollection(COLLECTION_NAME)).thenReturn(mongoCollection);
        when(mongoCollection.updateMany(filter, update)).thenReturn(updateResultPublisher);

        databaseUpdater.rollbackUpdateFieldInCollection(mongoClient);
        verify(mongoCollection).updateMany(filter, update);
    }

    @Test
    void addFieldToAllDocumentsTest() {

        Query query = Query.query(where(FIELD_NAME).exists(true));
        Update update = new Update().set(STATE_FIELD, "ACTIVE");

        UpdateResult updateResult = UpdateResult.acknowledged(1, 1L, null);

        when(reactiveMongoTemplate.updateMulti(query, update, COLLECTION_NAME))
                .thenReturn(Mono.just(updateResult));

        databaseUpdater.addFieldToAllDocuments(reactiveMongoTemplate);
        verify(reactiveMongoTemplate, times(1)).updateMulti(query, update, COLLECTION_NAME);
    }


    @Test
    void removeFieldToAllDocumentsTest() {

        Query query = Query.query(where(FIELD_NAME).exists(true));
        Update update = new Update().unset(STATE_FIELD);

        when(reactiveMongoTemplate.updateMulti(query, update, COLLECTION_NAME))
                .thenReturn(Mono.just(UpdateResult.acknowledged(1, 1L, null)));

        databaseUpdater.removeFieldToAllDocuments(reactiveMongoTemplate);
        verify(reactiveMongoTemplate, times(1)).updateMulti(query, update, COLLECTION_NAME);
    }

}

// Node: updateFieldInCollectionTest
// Node: rollbackUpdateFieldInCollectionTest
// Node: addFieldToAllDocumentsTest
// Node: acknowledged
// Node: removeFieldToAllDocumentsTest
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.reactivestreams.client.MongoClient;
import nl.altindag.log.LogCaptor;
import org.bson.Document;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
@SpringBootTest
class DataBaseRollBackTest {

    @Container
    static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:4.0.10")
            .withExposedPorts(27017)
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", () -> mongoDBContainer.getReplicaSetUrl("challenges"));
    }

    @Autowired
    private ReactiveMongoTemplate reactiveMongoTemplate;

    @Autowired
    private DataBaseRollback dataBaseRollback;

    @Autowired
    private MongoClient mongoClient;

    private LogCaptor logCaptor;

    @BeforeEach
    void setUp() {
        logCaptor = LogCaptor.forClass(DataBaseRollback.class);
    }

    @DisplayName("Test @Execution method - Verify thrown exception to demostrate rollback feature")
    @Test
    void ExecutionTest() {


        assertThrows(IllegalArgumentException.class, () -> dataBaseRollback.execution(mongoClient));
        assertTrue(logCaptor.getInfoLogs().contains("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution started"));

    }

    @DisplayName("Test @RollbackExecution method - Verify the rollback of the changes made in the execution method")
    @Test
    void rollbackTest() {
        dataBaseRollback.rollBackExecution(mongoClient);
        assertTrue(logCaptor.getInfoLogs().contains("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution started"));
        assertTrue(logCaptor.getInfoLogs().contains("Field updated in collection rolled back"));
        assertTrue(logCaptor.getInfoLogs().contains("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution completed successfully"));
    }

    @DisplayName("Test updateFieldInCollection method - Verify thrown exception when invalid operator is used")
    @Test
    void updateFieldInCollectionTest() {
        assertThrows(IllegalArgumentException.class, () -> dataBaseRollback.updateFieldInCollection(mongoClient));
        assertTrue(logCaptor.getErrorLogs().stream()
                .anyMatch(log -> log.contains("All update operators must start with '$', but 'invalidOperator' does not")));
    }

    @DisplayName("Test updateTextInField method - Verify the field is updated with the new value")
    @Test
    void updateTextInFieldTest() {

        reactiveMongoTemplate.save(new Document("Language Rollbacked", "LanguageDemo"), "mongockDemo").block();
        dataBaseRollback.updateTextInField(mongoClient);

        Document updatedDocument = reactiveMongoTemplate.findOne(
                new org.springframework.data.mongodb.core.query.Query(
                        org.springframework.data.mongodb.core.query.Criteria.where("Language Rollbacked").is("LanguageUpdated")),
                Document.class, "mongockDemo").block();

        assertNotNull(updatedDocument, "The document should be updated with the new value 'LanguageUpdated'");
    }


    @DisplayName("Test rollbackUpdateFieldInCollection method - Verify the field is renamed back to 'Language Rollbacked'")
    @Test
    void rollbackUpdateFieldInCollectionTest() {

        reactiveMongoTemplate.save(new Document("Language Name Updated", "someValue"), "mongockDemo").block();
        dataBaseRollback.rollbackUpdateFieldInCollection(mongoClient);

        Document rolledBackDocument = reactiveMongoTemplate.findOne(
                new org.springframework.data.mongodb.core.query.Query(
                        org.springframework.data.mongodb.core.query.Criteria.where("Language Rollbacked").exists(true)),
                Document.class, "mongockDemo").block();

        assertNotNull(rolledBackDocument, "The field should be renamed back to 'Language Rollbacked'");
    }



    @AfterEach
    void tearDown() {
        reactiveMongoTemplate.dropCollection("mongockDemo").block();
        logCaptor.close();
    }
}

// Node: getErrorLogs
// Node: updateTextInFieldTest
// Node: findOne
// Node: is
package com.itachallenge.challenge.config.dbchangelog;

import com.itachallenge.challenge.document.LanguageDocument;
import com.mongodb.reactivestreams.client.MongoDatabase;
import io.mongock.api.annotations.*;
import io.mongock.driver.mongodb.reactive.util.MongoSubscriberSync;
import io.mongock.driver.mongodb.reactive.util.SubscriberSync;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Component;

import java.util.UUID;

import static org.springframework.data.mongodb.core.query.Criteria.where;

@Component
@ChangeUnit(id = "DatabaseInitalizerTest", order = "1", author = "Ernesto Arcos / Pedro López")
public class TestDatabaseInitializer {
    Query query = new Query(where("_id").ne(null));
    private final Logger logger = LoggerFactory.getLogger(DatabaseInitializer.class);
    private static final String COLLECTION_NAME = "MongockTest";

    @BeforeExecution
    public void createCollection(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.createCollection(COLLECTION_NAME).subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockTest collection created");
    }

    @RollbackBeforeExecution
    public void rollbackBeforeExecution(MongoDatabase mongoDatabase) {
        SubscriberSync<Void> subscriber = new MongoSubscriberSync<>();

        mongoDatabase.getCollection(COLLECTION_NAME).drop().subscribe(subscriber);
        subscriber.await();

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~");
        logger.info("mongockTest collection droped");
    }

    @Execution
    public void execution(ReactiveMongoTemplate reactiveMongoTemplate) {
        LanguageDocument languageDocument = new LanguageDocument(UUID.randomUUID(), "LanguageDemo", "https://image-default.com/default.png");
        reactiveMongoTemplate.save(languageDocument, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nexecution"))
                .subscribe();
    }

    @RollbackExecution
    public void rollback(ReactiveMongoTemplate reactiveMongoTemplate) {
        reactiveMongoTemplate.remove(query, COLLECTION_NAME)
                .doOnSuccess(success -> logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nrollback"))
                .then();
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/config/dbchangelog/TestDatabaseInitializer.java:TestDatabaseInitializer.<init>
