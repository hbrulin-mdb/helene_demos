import com.mongodb.client.*;
import com.mongodb.client.model.Filters;
import org.bson.*;
import org.bson.types.Binary;

import java.util.*;

public class ExplicitQueryableEncryptionExample {

    public static void main(String[] args) {

        // Regular MongoDB client
        MongoClient mongoClient = MongoClients.create("mongodb://localhost:27017");
        MongoDatabase db = mongoClient.getDatabase("test");

        // KMS provider (example: local key)
        Map<String, Map<String, Object>> kmsProviders = Map.of(
            "local", Map.of(
                "key", Base64.getDecoder().decode(
                    "Mng0QjRFRkY0QjRFRkY0QjRFRkY0QjRFRkY0QjRFRkY0QjRFRkY0"
                )
            )
        );

        ClientEncryptionSettings clientEncryptionSettings =
            ClientEncryptionSettings.builder()
                .keyVaultMongoClientSettings(
                    MongoClientSettings.builder()
                        .applyConnectionString(
                            new ConnectionString("mongodb://localhost:27017"))
                        .build()
                )
                .keyVaultNamespace("encryption.__keyVault")
                .kmsProviders(kmsProviders)
                .build();

        ClientEncryption clientEncryption =
            ClientEncryptions.create(clientEncryptionSettings);

        // Encrypt a value explicitly
        BsonBinary encryptedSSN = clientEncryption.encrypt(
            new BsonString("123-45-6789"),
            new EncryptOptions("AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic")
                .keyId(getKeyId(clientEncryption))
        );

        MongoCollection<Document> coll = db.getCollection("people");

        // Insert encrypted field
        coll.insertOne(new Document("name", "Alice")
            .append("ssn", encryptedSSN));

        // Query using encrypted value
        Document result = coll.find(
            Filters.eq("ssn", encryptedSSN)
        ).first();

        System.out.println(result);
    }

    private static UUID getKeyId(ClientEncryption clientEncryption) {
        // Normally you’d create or look up a data key once and reuse it
        return clientEncryption.createDataKey("local");
    }
}
