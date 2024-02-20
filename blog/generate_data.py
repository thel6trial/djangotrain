from faker import Faker
import random
import json

fake = Faker()

data = []

for i in range(30, 50):  
    post = {
        "model": "blog.post",
        "pk": i + 1,
        "fields": {
            "postTitle": fake.sentence(),
            "postContent": fake.paragraph(),
            "postDate": fake.date_time().strftime("%Y-%m-%d %H:%M"),
            "postImage": None,
            "user": 4
        }
    }
    data.append(post)

with open('posts.json', 'w') as outfile:
    json.dump(data, outfile)