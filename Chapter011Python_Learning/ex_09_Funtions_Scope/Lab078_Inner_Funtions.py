def outer_funtions():
    var1 = 30

    def inner_funtion():
        var2 = 90
        print(var1)

    def inner_funtion2():
        print(var1)

    inner_funtion()
    inner_funtion2()


outer_funtions()
