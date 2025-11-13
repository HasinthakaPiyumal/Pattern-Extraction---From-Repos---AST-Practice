# Cluster 0

@partial(jax.pmap, axis_name='batch', static_broadcasted_argnums=(3, 4, 5, 6))
def p_generate(tokenized_prompt, key, params, top_k, top_p, temperature, condition_scale):
    return model.generate(**tokenized_prompt, prng_key=key, params=params, top_k=top_k, top_p=top_p, temperature=temperature, condition_scale=condition_scale)

@partial(jax.pmap, axis_name='batch')
def p_decode(indices, params):
    return vqgan.decode_code(indices, params=params)

