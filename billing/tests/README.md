
| Area | What We Test | Ensures That |
|------|---------------|--------------------------|
| POST /rates | Valid Excel parsing | Data is inserted correctly |
| POST /rates | Missing `file` field | Client input is validated |
| POST /rates | File not found | File location is validated |
| POST /rates | Empty parsed list | Content of file is validated |
| GET /rates | Empty DB | API returns a helpful message |
| GET /rates | DB contains records | API responds with `200 OK` |
