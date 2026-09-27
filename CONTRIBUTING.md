# Contributing to ANUSINT

We welcome contributions! Please follow these steps to contribute to the project:

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally: `git clone [https://github.com/your-username/anusint.git](https://github.com/your-username/anusint.git)`
3. **Create a new branch** for your feature or bug fix: `git checkout -b feature/your-feature-name`
4. **Install in development mode**: Run `pip install -e .` to map the CLI tool to your local environment.
5. **Run the tests**: Ensure all existing tests pass by running `python -m unittest discover tests`.
6. **Commit your changes**: Write clear, concise commit messages.
7. **Push to your fork** and submit a Pull Request.

## Coding Standards
* Ensure all new features include appropriate unit tests in the `tests/` directory.
* Maintain strict typing across new modules.
* Respect the core rate-limiting and backoff logic; do not introduce aggressive polling mechanisms.