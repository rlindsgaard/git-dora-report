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