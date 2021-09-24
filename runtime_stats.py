from matplotlib import pyplot as plt
import statistics

def show_runtimes_as_hist():
    with open("runtime_output_file.txt") as f:
        data = f.read()

    data = data.split('\n')
    data = [float(x) for x in data if x != '']
    data.sort()

    lo = int(data[0])
    hi = int(data[-1]+1)

    step = 0.5
    num_buckets = int((hi - lo) / step)
    buckets = [lo + i*step for i in range(num_buckets)]

    info = {
        'Mean': statistics.mean(data),
        'Stdev': statistics.stdev(data),
        'Min': lo,
        'Max': hi
    }

    for k, v in info.items():
        print(f"{k}\t{v}")

    plt.hist(data, bins=buckets)
    plt.show()


if __name__ == "__main__":
    show_runtimes_as_hist()