import com.mongodb.*;
import com.mongodb.client.*;
import org.bson.Document;

import java.util.*;

public class AutomaticQueryableEncryptionExample {

    public static void main(String[] args) {

        // KMS provider (example: local key)
        Map<String, Map<String, Object>> kmsProviders = Map.of(
            "local", Map.of(
                "key", Base64.getDecoder().decode(
                    "Mng0QjRFRkY0QjRFRkY0QjRFRkY0QjRFRkY0QjRFRkY0QjRFRkY0"
                )
            )
        );

        AutoEncryptionSettings autoEncryptionSettings =
            AutoEncryptionSettings.builder()
                .keyVaultNamespace("encryption.__keyVault")
                .kmsProviders(kmsProviders)
                .schemaMap(Map.of(
                    "test.people",
                    new Document("bsonType", "object")
                        .append("properties",
                            new Document("ssn",
                                new Document("encrypt",
                                    new Document("bsonType", "string")
                                        .append("algorithm",
                                            "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic")
                                        .append("keyId",
                                            List.of(new Document("$binary",
                                                new Document("base64", "<key-id-base64>")
                                                    .append("subType", "04")))))))
                ))
                .build();

        MongoClientSettings settings =
            MongoClientSettings.builder()
                .applyConnectionString(
                    new ConnectionString("mongodb://localhost:27017"))
                .autoEncryptionSettings(autoEncryptionSettings)
                .build();

        MongoClient client = MongoClients.create(settings);

        MongoCollection<Document> coll =
            client.getDatabase("test").getCollection("people");

        // Insert: plaintext in code, encrypted automatically
        coll.insertOne(new Document("name", "Alice")
            .append("ssn", "123-45-6789"));

        // Query: plaintext query
        Document result = coll.find(
            new Document("ssn", "123-45-6789")
        ).first();

        System.out.println(result);
    }
}
