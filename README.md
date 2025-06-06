# Phantom Mask
You are tasked with building a backend service and a database for a pharmacy platform, using only RESTful APIs for communication.

## A. Raw Data
1. [Pharmacy Data](data/pharmacies.json): This dataset contains a list of pharmacies with their names, opening hours, cash balances, and mask products.
2. [User Data](data/users.json): This dataset contains a list of users with their names, cash balances, and purchasing histories.

> These datasets are raw, meaning you can process and transform the data before loading it into your database.

## B. Task Requirements
This task is based on a development request from the PM. The goal is to build an API server with comprehensive documentation and a relational database to support integration and development by the frontend team.

The frontend team will rely on the API documentation to build the client application. Therefore, the API must be clear, complete, and support the following operations to ensure that the data can be accessed and interacted with quickly and intuitively.

The following are the required features:
1. List pharmacies, optionally filtered by specific time and/or day of the week.
2. List all masks sold by a given pharmacy with an option to sort by name or price.
3. List all pharmacies that offer a number of mask products within a given price range, where the count is above, below, or between given thresholds.
4. Show the top N users who spent the most on masks during a specific date range.
5. Process a purchase where a user buys masks from multiple pharmacies at once.
6. Update the stock quantity of an existing mask product by increasing or decreasing it.
7. Create or update multiple mask products for a pharmacy at once, including name, price, and stock quantity.
8. Search for pharmacies or masks by name and rank the results by relevance to the search term.

> If you find the requirements insufficiently detailed, design your solution to be as realistic and practical as possible.

## C. Deliverables
1. Fork or Copy this repository to your GitHub account.
2. Write an introduction to your work in [response.md](response.md).
3. Notify HR via email once you have completed the task. Include necessary details such as your GitHub account and the repository URL.

Must include in the repository:
1. Documentation for the API interface.
2. Commands to run the ETL (Extract, Transform, and Load) script, which processes the raw datasets and loads them into your database.
3. Commands to set up the server and database.
4. Provide clear and concise instructions for deploying the application locally.

Common mistakes to avoid:
1. Missing documentation.
2. A project that does not meet its functional requirements.
3. A solution that fails to meet the requirements.
4. Poor version control practices.

## D. Review Process
Your project will be reviewed by at least one backend engineer and evaluated according to the following criteria.
* **Requirement**
  * Has the implementation met all the task requirements defined in Part B
* **Design**
  * **Database**
    * Proper table normalization, clear column names & data types
    * Well-defined relationships; index planning balances performance & maintainability
    * Strong migration setup to ensure smooth deployment and rollback.
  * **API**
    * Does the database design meet the requirements and remain easy to understand and extend?
    * Is the raw data imported and cleaned effectively before being loaded into the database?
    * Does the API logic meet the requirements and reflect real-world scenarios?
  * **Architecture:**
    * Does the design pattern align with the framework's guidelines?
    * If using a framework, does the solution avoid reinventing the wheel?
* **Implementation**
  * **Code Quality**
    * **Readability**: Is the code easy to read and understand? Are naming conventions descriptive and consistent? Is the logic clear?
    * **Performance**: Is the code efficient? Does it avoid redundant computations or unnecessary queries?
    * **Maintainability**: Is the code modular and easy to maintain or extend? Does it include proper error handling and helpful comments?
  * **Completion**
    * Avoid any 5xx errors when the API is called.
    * Double-check for typos and grammatical mistakes before submission.
  * **Security**
    * Aligns with OWASP Top 10; prevents SQLi / XSS / CSRF, etc.
    * Secrets and keys are not hard-coded in source
* **Unit test**
  * Cover the primary success and failure scenarios, and a coverage report is available for verification.
  * Test cases are readable and independent.
* **Deployment**
  * The application should be deployable either locally (e.g., using Docker or other means) or on a free-tier cloud hosting platform (e.g., [fly.io](https://fly.io/docs/speedrun/), [render](https://render.com/docs/web-services), or similar).
  * If Docker is used, evaluation will include reviewing the Dockerfile and/or docker-compose configuration.
  * If other deployment methods are used, evaluation will focus on the clarity and completeness of the deployment steps and procedures.
* **Documentation**
  * Provide complete and consistent API documentation. Each endpoint should clearly describe:
    * Path and HTTP method
    * Request parameters (path, query, body)
    * Response format and examples
    * Error response format (including codes and messages) The documentation should be kept in sync with the codebase.
