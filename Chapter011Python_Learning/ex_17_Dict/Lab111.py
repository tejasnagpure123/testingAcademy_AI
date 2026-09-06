response_time_ms = [1200, 1500, 1800]


def mail_sec(x):
    return x / 1000


response_times_s = list(map(mail_sec, response_time_ms))
print(response_times_s)


response_times_L = list(map(lambda x: x / 1000, response_time_ms))
print(response_times_L)
