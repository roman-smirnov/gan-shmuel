access db docker compose exec billing-db mysql -u root -ppassword billdb 
build compose: docker compose up --build -d
run compose: docker compose up -d
stop compose: docker compose down
run all tests: docker compose exec billing-app pytest tests/
