from slither.slither import Slither

file = input('Enter file name or nothing for default: ')

if not file:
    file = 'contracts/Bank_RE.sol'
else:
    file = 'contracts/' + file




analyze = Slither(file)

for contract in analyze.contracts:
    for function in contract.functions:
        for node in function.all_nodes():
            if node.can_reenter():
                print(f'Function: {function} can be reentered.')
                print(node.all_slithir_operations()[0])
                break

#print(analyze.contracts[0].functions[0].all_nodes()[0].can_reenter())
