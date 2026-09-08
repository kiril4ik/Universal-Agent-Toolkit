# Go Rules
- Follow the declared Go version and `gofmt`, `go vet`, and test conventions.
- Keep interfaces small and consumer-owned where practical.
- Propagate/wrap errors with useful context; do not panic for expected errors.
- Pass `context.Context` through request/I/O boundaries.
- Avoid goroutine leaks and unbounded concurrency; define ownership and shutdown.
