
| Area | What We Test | Ensures That |
|------|---------------|--------------------------|
| POST /rates | Valid Excel parsing | Data is saved correctly to DB| 
| POST /rates | Missing file field | Client input is validated | 
| POST /rates | File not found | File location is validated | 
| POST /rates | returns empty list| Content of file is validated | 
| GET /rates | Empty DB | API returns a clear format error (400)| 
| GET /rates | DB contains records | API responds with 200 OK |
