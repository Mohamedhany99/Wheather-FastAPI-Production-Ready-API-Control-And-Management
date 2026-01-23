# Circuit Breaker Design Pattern - Complete Guide

## Table of Contents
1. [What is the Circuit Breaker Pattern?](#what-is-the-circuit-breaker-pattern)
2. [Why Do We Need It?](#why-do-we-need-it)
3. [How It Works](#how-it-works)
4. [The Three States](#the-three-states)
5. [State Transitions](#state-transitions)
6. [Our Implementation](#our-implementation)
7. [Code Walkthrough](#code-walkthrough)
8. [Real-World Example](#real-world-example)
9. [Configuration](#configuration)
10. [Benefits](#benefits)
11. [When to Use It](#when-to-use-it)

---

## What is the Circuit Breaker Pattern?

The **Circuit Breaker** is a design pattern used to detect failures and prevent an application from repeatedly trying to execute an operation that's likely to fail. It's named after electrical circuit breakers that protect electrical systems from damage.

### The Analogy

Think of an electrical circuit breaker in your home:
- **Normal operation (CLOSED)**: Electricity flows freely
- **Overload detected (OPEN)**: Breaker trips, stops flow immediately
- **Testing recovery (HALF-OPEN)**: After some time, breaker tests if the issue is resolved
- **If fixed (CLOSED)**: Electricity flows again
- **If still broken (OPEN)**: Breaker trips again

In software, it works the same way but protects your application from:
- Cascading failures
- Resource exhaustion
- Slow responses
- Repeated failures

---

## Why Do We Need It?

### The Problem: Cascading Failures

Imagine this scenario:

```
Your API → Weatherstack API
   ↓
Weatherstack API goes down
   ↓
Your API keeps trying to call it
   ↓
Each request waits 8 seconds (timeout)
   ↓
100 requests = 800 seconds of waiting
   ↓
Your API becomes slow/unresponsive
   ↓
Users experience poor performance
   ↓
Cascading failure spreads to your entire system
```

### The Solution: Circuit Breaker

```
Your API → Circuit Breaker → Weatherstack API
   ↓
Weatherstack API goes down
   ↓
Circuit Breaker detects failures
   ↓
After 5 failures, circuit opens
   ↓
Future requests fail FAST (milliseconds)
   ↓
Your API returns stale cache instead
   ↓
System remains responsive
   ↓
When Weatherstack recovers, circuit closes automatically
```

---

## How It Works

The circuit breaker monitors the success/failure of operations and acts as a gate:

1. **Tracks failures**: Counts consecutive failures and calculates failure rate
2. **Opens circuit**: When threshold is reached, stops allowing requests
3. **Fast failure**: Returns error immediately without waiting
4. **Tests recovery**: Periodically tests if the service is back
5. **Closes circuit**: When service recovers, allows requests again

---

## The Three States

### 1. CLOSED (Normal Operation)

**What it means:**
- Circuit is closed = requests flow through normally
- All requests are allowed to proceed
- Failures are tracked but don't stop requests

**Behavior:**
```python
Request → Circuit Breaker → API Call → Success/Failure
                              ↓
                         Track result
                              ↓
                         Continue normally
```

**When it's CLOSED:**
- Service is healthy
- Requests succeed
- Normal operation

---

### 2. OPEN (Failing - Fast Fail)

**What it means:**
- Circuit is open = requests are blocked immediately
- No API calls are made
- Returns error instantly (milliseconds instead of seconds)

**Behavior:**
```python
Request → Circuit Breaker → ❌ CircuitBreakerOpenError
                              ↓
                         Return immediately
                              ↓
                         No API call made
```

**When it opens:**
- 5 consecutive failures, OR
- Failure rate > 50% in recent requests

**Benefits:**
- Saves time (no waiting for timeouts)
- Saves resources (no wasted API calls)
- Prevents cascading failures

---

### 3. HALF_OPEN (Testing Recovery)

**What it means:**
- Circuit is half-open = testing if service recovered
- Allows ONE request to test
- Based on result, either closes or reopens

**Behavior:**
```python
Request → Circuit Breaker → Single API Call
                              ↓
                         Success? → CLOSED (recovered!)
                         Failure? → OPEN (still broken)
```

**When it enters HALF_OPEN:**
- After recovery timeout (60 seconds) passes while OPEN
- Automatically tests with next request

**Why HALF_OPEN?**
- Prevents flooding a recovering service
- Tests recovery safely
- Only one request at a time

---

## State Transitions

Here's the complete state machine:

```
┌─────────┐
│ CLOSED  │ ← Normal operation, requests flow through
└────┬────┘
     │
     │ 5 consecutive failures OR failure rate > 50%
     ↓
┌─────────┐
│  OPEN   │ ← Fast fail, no requests allowed
└────┬────┘
     │
     │ 60 seconds pass (recovery timeout)
     ↓
┌─────────────┐
│ HALF_OPEN   │ ← Testing recovery
└────┬────────┘
     │
     ├─ Success → CLOSED (recovered!)
     │
     └─ Failure → OPEN (still broken)
```

### Transition Rules

**CLOSED → OPEN:**
- Condition: `failures >= 5` OR `failure_rate >= 50%`
- Action: Stop all requests, start recovery timer

**OPEN → HALF_OPEN:**
- Condition: `time_since_opened >= 60 seconds`
- Action: Allow next request to test

**HALF_OPEN → CLOSED:**
- Condition: Request succeeds
- Action: Reset counters, resume normal operation

**HALF_OPEN → OPEN:**
- Condition: Request fails
- Action: Open circuit again, restart timer

---

## Our Implementation

### Class Structure

```python
class CircuitBreaker:
    def __init__(self):
        self.state = CircuitState.CLOSED
        self.failure_threshold = 5
        self.recovery_timeout = 60  # seconds
        self.failure_rate_threshold = 0.5  # 50%
        self.stats = CircuitBreakerStats()
        self._recent_requests = []  # Track last 20 requests
```

### Key Components

1. **State Management**: Tracks current state (CLOSED/OPEN/HALF_OPEN)
2. **Failure Tracking**: Counts failures and calculates failure rate
3. **Recovery Timer**: Tracks when circuit was opened
4. **Statistics**: Records successes, failures, state changes

---

## Code Walkthrough

### 1. The `call()` Method - Main Entry Point

```python
async def call(self, func: Callable, *args, **kwargs) -> Any:
    """Execute a function with circuit breaker protection."""
    
    # Check if we should attempt the request
    if not self._should_attempt_request():
        raise CircuitBreakerOpenError("Circuit breaker is OPEN")
    
    try:
        # Execute the function
        result = await func(*args, **kwargs)
        self._record_success()  # Track success
        return result
    except Exception:
        self._record_failure()  # Track failure
        raise  # Re-raise the exception
```

**What happens:**
- Checks circuit state
- If OPEN and timeout not passed → raise error immediately
- If CLOSED or HALF_OPEN → attempt request
- Track result (success/failure)
- Update state if needed

---

### 2. The `_should_attempt_request()` Method

```python
def _should_attempt_request(self) -> bool:
    if self.state == CircuitState.CLOSED:
        return True  # Always allow in CLOSED state
    
    if self.state == CircuitState.OPEN:
        # Check if recovery timeout passed
        if (time.time() - self.opened_at) >= self.recovery_timeout:
            self.state = CircuitState.HALF_OPEN  # Transition!
            return True
        return False  # Still in timeout period
    
    if self.state == CircuitState.HALF_OPEN:
        return True  # Allow one test request
    
    return False
```

**Logic:**
- CLOSED: Always allow
- OPEN: Only allow if timeout passed (transition to HALF_OPEN)
- HALF_OPEN: Allow (testing recovery)

---

### 3. The `_record_failure()` Method

```python
def _record_failure(self):
    self.stats.failures += 1
    self._recent_requests.append(False)
    
    if self.state == CircuitState.CLOSED:
        failure_rate = self._calculate_failure_rate()
        if (self.stats.failures >= self.failure_threshold or 
            failure_rate >= self.failure_rate_threshold):
            # Open the circuit!
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
    
    elif self.state == CircuitState.HALF_OPEN:
        # Test failed, reopen circuit
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
```

**What happens:**
- Increment failure counter
- Add to recent requests list
- Check if we should open circuit
- Update state if threshold reached

---

### 4. The `_record_success()` Method

```python
def _record_success(self):
    self.stats.successes += 1
    self._recent_requests.append(True)
    
    if self.state == CircuitState.HALF_OPEN:
        # Recovery successful!
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.stats.failures = 0  # Reset counter
```

**What happens:**
- Increment success counter
- Add to recent requests list
- If HALF_OPEN, transition to CLOSED (recovered!)

---

### 5. Failure Rate Calculation

```python
def _calculate_failure_rate(self) -> float:
    if not self._recent_requests:
        return 0.0
    failures = sum(1 for r in self._recent_requests if not r)
    return failures / len(self._recent_requests)
```

**What it does:**
- Tracks last 20 requests
- Calculates percentage of failures
- Used as alternative trigger (50% failure rate)

---

## Real-World Example

### Scenario: Weatherstack API Goes Down

**Timeline:**

```
00:00 - Request 1 → Weatherstack API → ❌ Timeout (8s)
00:08 - Request 2 → Weatherstack API → ❌ Timeout (8s)
00:16 - Request 3 → Weatherstack API → ❌ Timeout (8s)
00:24 - Request 4 → Weatherstack API → ❌ Timeout (8s)
00:32 - Request 5 → Weatherstack API → ❌ Timeout (8s)
00:40 - Circuit Breaker: "5 failures detected, OPENING circuit"
00:40 - Request 6 → Circuit Breaker → ❌ CircuitBreakerOpenError (0.001s)
00:40 - Request 7 → Circuit Breaker → ❌ CircuitBreakerOpenError (0.001s)
00:40 - Request 8 → Circuit Breaker → ❌ CircuitBreakerOpenError (0.001s)
...
01:40 - Circuit Breaker: "60 seconds passed, entering HALF_OPEN"
01:40 - Request 9 → Circuit Breaker → Weatherstack API → ✅ Success!
01:40 - Circuit Breaker: "Recovery successful, CLOSING circuit"
01:40 - Request 10 → Circuit Breaker → Weatherstack API → ✅ Success
01:40 - Normal operation resumed
```

**Without Circuit Breaker:**
- Each request waits 8 seconds
- 100 requests = 800 seconds wasted
- System becomes slow/unresponsive

**With Circuit Breaker:**
- First 5 requests: 40 seconds (detection)
- Remaining requests: Instant failure (0.001s each)
- System remains responsive
- Automatic recovery when API comes back

---

## Configuration

### Default Settings

```python
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5        # Consecutive failures
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60        # Seconds
CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD = 0.5 # 50%
```

### Customization

You can adjust these in `.env`:

```bash
# More sensitive (opens faster)
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD=0.3

# Less sensitive (tolerates more failures)
CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD=0.7

# Faster recovery testing
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30

# Slower recovery testing
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=120
```

---

## Benefits

### 1. **Prevents Cascading Failures**
- Stops failures from spreading
- Protects your entire system

### 2. **Fast Failure**
- Milliseconds instead of seconds
- Better user experience

### 3. **Resource Conservation**
- No wasted API calls
- No waiting for timeouts
- Saves CPU, memory, network

### 4. **Automatic Recovery**
- No manual intervention needed
- Tests recovery automatically
- Resumes when service is back

### 5. **Observability**
- Tracks state changes
- Records statistics
- Integrates with metrics

---

## When to Use It

### ✅ Good Use Cases

1. **External API Calls**
   - Third-party services
   - Microservices
   - Database connections

2. **Unreliable Services**
   - Services with known issues
   - Services with rate limits
   - Services with timeouts

3. **Critical Paths**
   - Operations that can cascade
   - High-traffic endpoints
   - User-facing features

### ❌ Not Suitable For

1. **Internal Operations**
   - Simple calculations
   - In-memory operations
   - Deterministic functions

2. **Always-Fail Operations**
   - Invalid inputs
   - Business logic errors
   - Authentication failures

3. **Very Fast Operations**
   - Operations < 1ms
   - No external dependencies
   - No failure scenarios

---

## Integration in Our Codebase

### How It's Used

```python
# In weather endpoint
try:
    weather_data = await circuit_breaker.call(
        weatherstack_service.get_current_weather, 
        city
    )
except CircuitBreakerOpenError:
    # Circuit is open, use stale cache
    stale_data = cache.get_stale(cache_key)
    return stale_data
```

### Flow Diagram

```
User Request
    ↓
Check Cache (fresh)
    ↓ (miss)
Circuit Breaker Check
    ├─ CLOSED → Call Weatherstack API
    ├─ OPEN → Return stale cache (fast!)
    └─ HALF_OPEN → Test call, then decide
    ↓
Track Result
    ↓
Update Circuit State
    ↓
Return Response
```

---

## Monitoring

### State Information

You can check circuit breaker state:

```python
state = circuit_breaker.get_state()
# Returns:
{
    "state": "closed",  # or "open" or "half_open"
    "failures": 3,
    "successes": 150,
    "failure_rate": 0.02,
    "opened_at": None,
    "state_changes": 2
}
```

### Metrics Integration

The circuit breaker integrates with our metrics system:
- Tracks when circuit opens
- Records state changes
- Monitors failure rates

---

## Best Practices

### 1. **Tune Thresholds Carefully**
- Too low: Opens too easily (false positives)
- Too high: Opens too late (damage done)
- Start with defaults, adjust based on monitoring

### 2. **Monitor State Changes**
- Alert when circuit opens
- Track recovery times
- Analyze failure patterns

### 3. **Combine with Fallbacks**
- Use stale cache when open
- Provide default responses
- Graceful degradation

### 4. **Test Recovery**
- Simulate failures
- Test state transitions
- Verify automatic recovery

---

## Summary

The Circuit Breaker pattern is a **resilience mechanism** that:

1. **Detects failures** by tracking success/failure rates
2. **Prevents cascading failures** by stopping requests when service is down
3. **Fails fast** by returning errors immediately (milliseconds)
4. **Recovers automatically** by testing when service might be back
5. **Protects resources** by avoiding wasted API calls

In our implementation:
- **3 states**: CLOSED, OPEN, HALF_OPEN
- **2 triggers**: Consecutive failures OR failure rate
- **Automatic recovery**: Tests after timeout
- **Integrated**: Works with cache fallback and metrics

It's a critical component of production-ready systems, ensuring your application remains responsive even when external dependencies fail.

---

## Further Reading

- [Martin Fowler's Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Resilience Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- Our implementation: `app/middleware/circuit_breaker.py`
- Usage: `app/api/routes/weather.py`
