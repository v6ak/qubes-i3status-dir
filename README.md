# Drop-in replacement for qubes-i3status

This is a work-in-progress. The ultimate goal is to develop a drop-in replacement for the current Bash-based qubes-i3status that preserves its behavior (except bugs and CPU load). It is a wrapper around i3status. That is, the config file for i3status adds some placeholders. My script just calls i3status and enhances its output using *interceptors*. This is the idiomatic way to enhance i3status.

This way should allow both easier development (i.e., not to reimplement the existing parts of i3status) and user configuration.

There are two versions:

* i3status-wrapper.py – this one uses synchronous code. I was unable to implement skipping lines there, so if the computation takes longer than the interval on average, the status	gets more and more delayed. While the initial situation is definitely not desired, the reaction is not appropriate.
* i3status-wrapper-async.py – rewrite of i3status-wrapper.py using asyncio. It has all the features of i3status-wrapper.py plus it implements status skipping when interceptors take too long time.


## Profiling

You can optionally profile interceptors in several ways:

* `--profile-interceptors` – this measures execution time of all the interceptors. Additonally, it tracks how many times an interceptor has exceeded 100ms. This threshold might be changed (probably lowered) in the future.
* `--profile-skipped-statuses` (only in async implementation) – this measures how many times was a status skipped. Skipping happens when the processing takes too much time.

## Restarting

Just send USR1 to the wrapper, it will do best-effort restart. Unless the protocol version of i3status changes, it should work. When the protocol version changes, it does not announce the new version.


## Status of implementation of all the fields

| Feature       | Type        | Implemented | Feature-complete | Optimizations planned  | Visually done |
| ------------- | ----------- | ----------- | ---------------- | ---------------------  | ------------- |
| Running qubes | Intercepted | Yes         | Yes              | Yes, the code is hacky | Yes           |
| Disk info     | Intercepted | Yes         | Hopefully**      | No                     | Yes           |
| Battery       | Native      | Yes         | Probably         | No                     | No            |
| Load          | Native      | Yes         | Probably         | No                     | Maybe         |
| Time          | Native      | Yes         | Yes              | No                     | Yes           |
| NetVM status* | N/A         | No*         | N/A              | N/A                    | N/A           |

\*) In the Bash-based qubes-i3status, this feature is commented and discouraged from usage for security reasons. For this reason, I did not consider this to be high priority. We can achieve feature parity even without implementing this feature.
\*\*) We need to test that it can properly handle changes of default_pool.


## Some other limitations

* When the wrapper script exits, it generates some nasty exceptions. While this is not nice, it does not prevent the script from working. But I see, this should be adjusted.
* The wrapper scripts do not properly recognize i3status startup failures.
* The async script does not recognize that the i3status has exited.


## License

1. As long as you do not require the autor to be liable of any damages caused by this software, just do what the f*ck you want to!
2. This agreement shall be construed in accordance with and governed by the laws of the Free Republic of Liberland.
