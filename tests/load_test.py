import time
import requests
import statistics
import concurrent.futures

# --- CONFIGURATION ---
URL = "http://127.0.0.1:8000/api/jobs/1/match" # Make sure Job #1 exists!
TOTAL_REQUESTS = 100
CONCURRENT_THREADS = 50 # How many requests hit the server at the exact same time

def fetch_match(req_id):
    """Hits the endpoint and returns the status code and time taken in milliseconds."""
    start_time = time.perf_counter()
    try:
        response = requests.get(URL, timeout=15)
        status = response.status_code
    except Exception as e:
        status = f"Failed: {e}"
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    return status, duration_ms

def run_load_test():
    print(f"🚀 Starting load test: {TOTAL_REQUESTS} requests with {CONCURRENT_THREADS} concurrent threads...")
    
    latencies = []
    success_count = 0
    error_count = 0
    
    # Start the global timer
    global_start = time.perf_counter()
    
    # Create a pool of concurrent threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_THREADS) as executor:
        # Submit all 100 tasks to the executor
        futures = [executor.submit(fetch_match, i) for i in range(TOTAL_REQUESTS)]
        
        # Gather the results as they finish
        for future in concurrent.futures.as_completed(futures):
            status, duration = future.result()
            if status == 200:
                success_count += 1
                latencies.append(duration)
            else:
                error_count += 1
                
    global_duration_sec = time.perf_counter() - global_start
    
    # --- CALCULATE METRICS ---
    if latencies:
        avg_latency = statistics.mean(latencies)
        p90_latency = statistics.quantiles(latencies, n=10)[8] # 90th percentile
        p95_latency = statistics.quantiles(latencies, n=20)[18] # 95th percentile
        rps = TOTAL_REQUESTS / global_duration_sec
        
        print("\n" + "="*40)
        print("📊 LOAD TEST RESULTS")
        print("="*40)
        print(f"Total Time:      {global_duration_sec:.2f} seconds")
        print(f"Success Rate:    {success_count}/{TOTAL_REQUESTS} ({success_count/TOTAL_REQUESTS * 100:.1f}%)")
        print(f"Error Rate:      {error_count}/{TOTAL_REQUESTS}")
        print(f"Throughput:      {rps:.1f} Requests Per Second (RPS)")
        print("-" * 40)
        print(f"Average Latency: {avg_latency:.2f} ms")
        print(f"Min Latency:     {min(latencies):.2f} ms")
        print(f"Max Latency:     {max(latencies):.2f} ms")
        print(f"P90 Latency:     {p90_latency:.2f} ms (90% of requests were faster than this)")
        print(f"P95 Latency:     {p95_latency:.2f} ms (95% of requests were faster than this)")
        print("="*40)
    else:
        print("❌ All requests failed. Check if your server is running!")

if __name__ == "__main__":
    run_load_test()