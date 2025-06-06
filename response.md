# Response
> The Current content is an **example template**; please edit it to fit your style and content.

## Requirement Completion Rate
* [ ] List pharmacies, optionally filtered by specific time and/or day of the week.
  * Implemented at xxx API.
* [ ] List all masks sold by a given pharmacy with an option to sort by name or price.
  * Implemented at xxx API.
* [ ] List all pharmacies that offer a number of mask products within a given price range, where the count is above, below, or between given thresholds.
  * Implemented at xxx API.
* [ ] Show the top N users who spent the most on masks during a specific date range.
  * Implemented at xxx API.
* [ ] Process a purchase where a user buys masks from multiple pharmacies at once.
  *  Implemented at xxx API.
* [ ] Update the stock quantity of an existing mask product by increasing or decreasing it.
  * Implemented at xxx API.
* [ ] Create or update multiple mask products for a pharmacy at once, including name, price, and stock quantity.
  * Implemented at xxx API.
* [ ] Search for pharmacies or masks by name and rank the results by relevance to the search term.
  * Implemented at xxx API.

## API Document
> * Please describe how to use the API in the API documentation.
> * You can edit by any format (e.g., Markdown or OpenAPI) or free tools (e.g., [hackMD](https://hackmd.io/), [postman](https://www.postman.com/), [google docs](https://docs.google.com/document/u/0/), or  [swagger](https://swagger.io/specification/)).

## Import Data Commands
Please run these two script commands to migrate the data into the database.

```bash
$ rake import_data:pharmacies[PATH_TO_FILE]
$ rake import_data:users[PATH_TO_FILE]
```

## Test Coverage Report
I wrote down the xx unit tests for the APIs I built. Please check the test coverage report here.

You can run the test script by using the command below:

```bash
bundle exec rspec spec
```

## Deployment
* To deploy the project locally using Docker, run the following commands:

```bash
# Build the Docker image with development environment
$ docker build --build-arg ENV=development -t my-project:1.0.0 .

# Start the service using docker-compose
$ docker-compose up -d

# Access the container to run data import tasks
$ docker exec -it my-project bash
$ rake import_data:pharmacies[PATH_TO_FILE]
$ rake import_data:user[PATH_TO_FILE]
```

* If you do not use Docker, please provide detailed instructions including the following:
1. Environment Requirements
2. Build & Run Steps

```bash
# Install dependencies
$ bundle install

# Set up the database (sample config/database.yml may be provided)
$ rails db:setup

# Import data
$ rake import_data:pharmacies[PATH_TO_FILE]
$ rake import_data:user[PATH_TO_FILE]

# Start the server
$ rails server
```

> * If any environment variables are required, please include instructions (e.g., create a .env file).
> * If the project relies on special permissions, external services, or third-party APIs, be sure to include setup and initialization steps.

* If you have deployed the demo site, please provid the demo site url.
> The demo site is ready on my AWS demo site; you can try any APIs on this demo site.

**This ensures others can deploy the project successfully, whether or not they are using Docker.**

## Additional Data
> If you have an ERD or any other materials that could help with understanding the system, please include them here.
