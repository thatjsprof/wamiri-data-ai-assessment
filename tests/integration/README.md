Integration tests normally spin up Postgres + Redis + localstack (AWS).
For this assessment, keep integration tests light to avoid complex setup.
Recommended additions (if you want extra points):
- Use `testcontainers` to start Postgres/Redis.
- Use `localstack` for Textract/S3 simulation.
