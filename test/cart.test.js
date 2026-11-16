import { test } from 'node:test'
import assert from 'node:assert/strict'
import { subtotal } from '../src/cart.js'

test('subtotal adds price times quantity', () => {
  assert.equal(subtotal([{ priceCents: 450, qty: 2 }, { priceCents: 300, qty: 1 }]), 1200)
})
