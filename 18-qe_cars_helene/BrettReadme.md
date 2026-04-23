# README

This project consists of a FastAPI backend server and a PyQt6 graphical client. The backend interfaces with a MongoDB database using **Queryable Encryption** to ensure sensitive fields (`VIN` and `licensePlate`) are encrypted at rest but can still be queried. 

## Features
* **FastAPI Server**: High-performance async API server.
* **MongoDB Queryable Encryption**: Uses a Local KMS provider to encrypt sensitive data (VIN, License Plate) before it hits the database, while still allowing prefix-based searches.
* **Dynamic Data Generation**: Generates thousands of realistic mock vehicle records using the `Faker` library.
* **PyQt6 Client**: A desktop application featuring debounce-enabled searching, bulk inserting, dynamic data tables, and live UI configuration.

---

## Prerequisites

1. **Python 3.8+**
2. **MongoDB Enterprise or MongoDB Atlas (7.0+)**: Queryable Encryption (specifically `prefixPreview` queries) requires a compatible MongoDB version.
3. **MongoDB Shared Encryption Library**: Your system must have the `crypt_shared` library (or `mongocryptd`) installed and available on the system path for PyMongo to perform auto-encryption.

---

## Installation

1. Install the required Python dependencies. Note that `pymongo[encryption]` is explicitly required to pull in `pymongo-crypt` for Queryable Encryption support.

```bash
pip3 install fastapi uvicorn pydantic "pymongo[encryption]" faker PyQt6 requests
```

---

## Running the Server (`main.py`)

The server is configured via command-line arguments. By default, it runs on HTTP, but you can provide certificates to run it over HTTPS.

### Basic Run (HTTP & Local MongoDB)
```bash
python main.py --mongo "mongodb://127.0.0.1:27017" --srv-port 8000
```

### Advanced Run (HTTPS Server & TLS MongoDB Connection)
If your MongoDB cluster requires TLS (e.g., an Atlas cluster or strict Enterprise deployment) and you want your FastAPI server to serve over HTTPS:

```bash
python main.py \\
    --mongo "mongodb+srv://<user>:<password>@cluster.mongodb.net/" \\
    --mongo-ca "./mongo-ca.pem" \\
    --mongo-pem "./mongo-client.pem" \\
    --srv-cert "./server-cert.pem" \\
    --srv-key "./server-key.pem" \\
    --srv-port 8443
```

### Server Command Line Arguments
* `--mongo`: (Required) MongoDB connection string.
* `--mongo-ca`: Path to the CA certificate for the MongoDB connection.
* `--mongo-pem`: Path to the client PEM file for MongoDB TLS.
* `--srv-cert`: Path to the SSL certificate for the FastAPI server (enables HTTPS).
* `--srv-key`: Path to the SSL key for the FastAPI server.
* `--srv-port`: Port for the FastAPI server to listen on (Default: `8000`).

---

## Running the Client (`client.py`)

Once the server is running, open a new terminal window and launch the PyQt6 client:

```bash
python client.py
```

### Using the Application

1. **Settings Tab**: 
   * If you changed the server port or enabled HTTPS, go to the Settings tab first.
   * Update the **Server URL** (e.g., `https://localhost:8443`) and click **Apply Settings**.
   * You can also dynamically adjust the application's font size here.
2. **Insert Tab**: 
   * Choose the number of mock vehicles you wish to generate (default: 1000).
   * Click **Insert Documents**. The server will generate realistic data, encrypt the `VIN` and `licensePlate` fields, and store them in MongoDB.
   * The table below will automatically refresh to show the top 1000 documents in the database.
3. **Search Tab**: 
   * Select a field to search by (`VIN`, `licensePlate`, or `model`).
   * Start typing in the text box. A 500ms debounce timer ensures the application doesn't overload the server. *Note: Prefix queries require at least 3 characters to trigger a search.*

---

## Important Security Note regarding KMS
In `main.py`, the **Local KMS Provider Key** is hardcoded for demonstration purposes:
```python
"key": b64decode("b7csKuW8B1zoGeA+JLg...")
```
**Do not use a hardcoded local key in a production environment.** For production deployments, integrate a proper Key Management Service (AWS KMS, Azure Key Vault, Google Cloud KMS, or KMIP) and securely pass credentials to the PyMongo `AutoEncryptionOpts`.

