def find_measurable_comparisons(fgraph: FunctionGraph, node: Apply) -> list[TensorVariable] | None:
    measurable_inputs = filter_measurable_variables(node.inputs)

    if len(measurable_inputs) != 1:
        return None

    # Make the measurable base_var always be the first input to the MeasurableComparison node
    [measurable_var] = measurable_inputs
    measurable_var_idx = node.inputs.index(measurable_var)

    # deny broadcasting of the measurable input
    if measurable_var.type.broadcastable != node.outputs[0].type.broadcastable:
        return None

    # Check that the other input is not potentially measurable, in which case this rewrite
    # would be invalid
    const = cast(TensorVariable, node.inputs[(measurable_var_idx + 1) % 2])

    # check for potential measurability of const
    if check_potential_measurability([const]):
        return None

    node_scalar_op = node.op.scalar_op

    # Change the Op if the base_var is the second input in node.inputs. e.g. pt.lt(const, dist) -> pt.gt(dist, const)
    if measurable_var_idx == 1:
        if isinstance(node_scalar_op, LT):
            node_scalar_op = GT()
        elif isinstance(node_scalar_op, GT):
            node_scalar_op = LT()
        elif isinstance(node_scalar_op, GE):
            node_scalar_op = LE()
        elif isinstance(node_scalar_op, LE):
            node_scalar_op = GE()

    compared_op = MeasurableComparison(node_scalar_op)
    compared_rv = compared_op.make_node(measurable_var, const).default_output()
    return [compared_rv]
