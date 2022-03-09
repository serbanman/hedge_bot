# input1 = ''
with open('input.txt', 'r') as file:
    input1 = file.readline()

input1 = input1.split()
input2 = int(input1[1])
input1 = int(input1[0])

with open('output.txt', 'w') as file:
    file.write(str(input1+input2))
