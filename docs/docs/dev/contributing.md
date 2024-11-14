Please fork our repository, implement the additions or changes you need, and then create a pull request. We are very open to merging your code into the upstream.

All new features should be configurable. After implementing the changes, ensure there is a configuration variable to enable or disable them. For example, if you do not provide `POLYGON_IO_API_KEY`, this data source will not be used.

### Code Formatting Guidelines

#### Frontend Formatting

To ensure consistent code style in the Frontend, please execute the following command after making any code changes:

```
npm run format
```

#### Backend Formatting

For maintaining uniformity in the Backend codebase, please use the `black` formatter. Follow these steps:

1. Install `black` if you haven't already:

    pip install black

1. Format your code by running:

    black .

#### Docs Formatting

Documentation is formatted using `mdformat` to maintain clarity and consistency in our Markdown files. Please run the following command to format your documentation:

```
mdformat .
```

Following these guidelines helps keep the codebase clean, readable, and easier to navigate for all contributors.
