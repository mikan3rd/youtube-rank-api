import firebase_admin
from firebase_admin import credentials, firestore
from settings import GOOGLE_TIKTOK_CLIENT_EMAIL, GOOGLE_TIKTOK_PRIVATE_KEY


def batch_update(collection, data_list, unique_key=None):
    initialize_firebase()
    db = firestore.client()
    batch = db.batch()
    ref = db.collection(collection)

    for num, data in enumerate(data_list, 1):

        if num % 500 == 0:
            batch.commit()
            batch = db.batch()
            ref = db.collection(collection)
            print("commit")

        data['update_at'] = firestore.SERVER_TIMESTAMP
        docs = ref.where(unique_key, '==', data.get(unique_key)).get()
        result = [doc for doc in docs]

        if result:
            print("update:", num)
            _id = result[0].id
            prev_data = result[0].to_dict()

            for k, v in data.items():
                if isinstance(v, dict) and prev_data.get(k):
                    prev_data[k].update(v)
                    data[k] = prev_data[k]

            batch.update(ref.document(_id), data)
            continue

        data['create_at'] = firestore.SERVER_TIMESTAMP
        batch.set(ref.document(), data)
        print("set:", num)

    # Commit the batch
    batch.commit()
    print("commit")


def initialize_firebase():
    if len(firebase_admin._apps) > 0:
        return

    cert = {
        "type": "service_account",
        "project_id": "mikan-test-845c3",
        "private_key_id": "f44d9227f465285a14f8cd47d027f3c2761d8586",
        "private_key": GOOGLE_TIKTOK_PRIVATE_KEY,
        "client_email": GOOGLE_TIKTOK_CLIENT_EMAIL,
        "client_id": "112880427431271489400",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-u2tv9%40mikan-test-845c3.iam.gserviceaccount.com"
    }
    cred = credentials.Certificate(cert)
    firebase_admin.initialize_app(cred)
