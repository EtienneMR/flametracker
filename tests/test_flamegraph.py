import json
from random import shuffle

from flametracker import Tracker


def swap(arr, i, j):
    arr[i], arr[j] = arr[j], arr[i]


@Tracker.wrap
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                swap(arr, j, j + 1)
    return arr


@Tracker.wrap
def find_min_index(arr, start):
    min_idx = start
    for j in range(start + 1, len(arr)):
        if arr[j] < arr[min_idx]:
            min_idx = j
    return min_idx


@Tracker.wrap
def selection_sort(arr):
    for i in range(len(arr)):
        min_idx = find_min_index(arr, i)
        arr[i], arr[min_idx] = arr[min_idx], arr[i]  # Swap
    return arr


@Tracker.wrap
def shift_elements(arr, start, end):
    for j in range(end, start, -1):
        arr[j] = arr[j - 1]


@Tracker.wrap
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            j -= 1
        shift_elements(arr, j + 1, i)
        arr[j + 1] = key
    return arr


@Tracker.wrap
def merge(left_half, right_half):
    merged = []
    i = j = 0
    while i < len(left_half) and j < len(right_half):
        if left_half[i] < right_half[j]:
            merged.append(left_half[i])
            i += 1
        else:
            merged.append(right_half[j])
            j += 1
    merged.extend(left_half[i:])
    merged.extend(right_half[j:])
    return merged


@Tracker.wrap
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid])
    right_half = merge_sort(arr[mid:])
    return merge(left_half, right_half)


@Tracker.wrap
def partition(arr):
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return left, middle, right


@Tracker.wrap
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    left, middle, right = partition(arr)
    return quick_sort(left) + middle + quick_sort(right)


def test_splited():
    with Tracker() as tracker:
        arr = list(range(10**3))
        shuffle(arr)
        bubble_sort(arr[:])
        selection_sort(arr[:])
        insertion_sort(arr[:])
        merge_sort(arr[:])
        quick_sort(arr[:])
    with open("tests/flamegraphs/splited.html", "w", encoding="utf-8") as f:
        f.write(tracker.to_flamegraph(splited=True))


def test_str():
    with Tracker() as tracker:
        arr = list(range(10**2))
        shuffle(arr)
        bubble_sort(arr[:])
        selection_sort(arr[:])
        insertion_sort(arr[:])
        merge_sort(arr[:])
        quick_sort(arr[:])
    with open("tests/flamegraphs/str.txt", "w", encoding="utf-8") as f:
        f.write(tracker.to_str())


def test_dict():
    with Tracker() as tracker:
        arr = list(range(10**2))
        shuffle(arr)
        bubble_sort(arr[:])
        selection_sort(arr[:])
        insertion_sort(arr[:])
        merge_sort(arr[:])
        quick_sort(arr[:])
    with open("tests/flamegraphs/dict.json", "w", encoding="utf-8") as f:
        json.dump(tracker.to_dict(), f, indent=4)


def test_calls():
    with Tracker() as tracker:
        for i in range(1, 4):
            with Tracker.action(f"Benchmark {10**i} elements"):
                print(f"Generating {10**i} elements")
                with Tracker.action("Generate", 10**i):
                    arr = list(range(10**i))
                    shuffle(arr)
                print("Sorting")
                merge_sort(arr[:])
                quick_sort(arr[:])

    print("Generating render")
    render = tracker.to_render(0.01, True)
    print("Generating flamegraph")
    with open("tests/flamegraphs/calls.html", "w", encoding="utf-8") as f:
        f.write(render.to_flamegraph(False))
