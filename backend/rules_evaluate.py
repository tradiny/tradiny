import logging 

def get_key(indicators, side, rule):
    type_key = f"type{side}"
    if rule[type_key] == "indicator":
        indicator_key = f"indicator{side}"
        output_key = f"output{side}"
        base = indicators[rule[indicator_key]]["indicator"]["id"]
        output = rule[output_key]
        return f"{base}-{output}"
    elif rule[type_key] == "data":
        source = f"source{side}"
        name = f"name{side}"
        interval = f"interval{side}"
        key = f"key{side}"
        return f"{rule[source]}-{rule[name]}-{rule[interval]}-{rule[key]}"
    elif rule[type_key] == "value":
        return "value"

def get_change(previous, current):
    if current == previous:
        return 0.0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0.0

def evaluate(rules, operators):
    rules = ["True" if rule else "False" for rule in rules]

    expression = [None] * (len(rules) + len(operators))
    expression[::2] = rules
    expression[1::2] = operators

    expression = " ".join(expression)

    return eval(expression)

def rules_evaluate(rules, operators, indicators, lastDataPoint):

    rules_evaluated = []

    for rule in rules:
        k1 = get_key(indicators, "1", rule)
        k2 = get_key(indicators, "2", rule)

        if k1 not in ["value"] and k1 not in lastDataPoint:
            logging.info(f"do not have data {k1}; has keys {lastDataPoint.keys()}")
            return None
        if k2 not in ["value"] and k2 not in lastDataPoint:
            logging.info(f"do not have data {k2}; has keys {lastDataPoint.keys()}")
            return None

        if k1 == "value":
            v1 = float(f"{rule['value1']}")
        else:
            v1 = float(lastDataPoint[k1])

        if k2 == "value":
            v2 = float(f"{rule['value2']}")
        else:
            v2 = float(lastDataPoint[k2])

        if rule["comparator"] == "<":
            rules_evaluated.append(v1 < v2)
        elif rule["comparator"] == ">":
            rules_evaluated.append(v1 > v2)
        elif rule["comparator"] == "near":
            percent = float(rule["near"])
            rules_evaluated.append(get_change(v1, v2) < percent)

    result = evaluate(rules_evaluated, operators)

    return result
