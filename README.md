# Git DORA Report

Use the git history to generate a DORA report.

## Assumptions

- Merge commits designate events that are used as data points.
- The existence of a specific tag (e.g. build-1234) on the merge commit indicates success.

## Metrics
### Deployment Frequency
Every merge commit is considered "a deployment", we track the time between each

### Change Failure Rate
If the tag specified is not found on the merge commit it is considered a failure.

### Mean Time to Recover
We count the mean time only for the event's where the state is "recovery"

### Lead Time for Changes
This really needs an external data point. There is no external collectors so we naively assume that work started at the first commit of the branch and calculate our lead time to merge from then.

## Code Guidelines
- Keep functions small
- Refactor existing logic when adding features
- Write appropriate log messages
- Use docstrings and PEP287 to explain functionality
- Inline document complicated code
- Lint using isort and in that order
- Use pytest
- Ensure test-suite passes for new changes
- Prefer using mocks, fixtures and fakers for conducting unit tests
- Exceptional conditions should be covered by unit tests
- main function should be covered by at least one integration/end-to-end test
- Prefer to use literal values when asserting during tests
- Use convential commits to format commit messages