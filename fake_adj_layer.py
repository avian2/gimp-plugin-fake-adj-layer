from gimpfu import *
from scipy.optimize import least_squares
import numpy as np

class Layer(object):
	def __init__(self, name, value, mode, opacity):
		self.name = name
		self.value = value
		self.mode = mode
		self.opacity = opacity

	def __repr__(self):
		return "Layer(name=%r, value=%r, mode=%r, opacity=%r)" % (
				self.name, self.value, self.mode, self.opacity)

def approx_gamma_poly(g):

	def soft_light(x, p):
		return x*(1.-p) + x*x*p

	def gamma(x, p):
		y = x
		for n in range(len(p)):
			y = soft_light(y, p[n])

		return y

	def func(p, g):
		x = np.linspace(0, 1, 100)

		yt = x**g
		y = gamma(x, p)

		return yt - y

	N = 4
	r = least_squares(func, [1]*N, bounds=[[0]*N,[1]*N], args=(g,))

	stack = []

	for n in range(N):
		layer = Layer(name="[adjust gamma %d]" % n, value=0, mode="soft light", opacity=r.x[n])
		stack.append(layer)

	return stack

def approx_gamma_lin(g):
	def div(x, f, p):
		return x*(1-p) + np.clip(x/f, 0, 1)*p

	def gamma(x, p):
		y = x
		for n in range(0, len(p), 2):
			y = div(y, p[n], p[n+1])

		return y

	def func(p, g):
		x = np.linspace(0, 1, 100)

		yt = x**g
		y = gamma(x, p)

		return yt - y

	N = 4
	r = least_squares(func, [1]*N*2, bounds=[[0]*N*2,[1]*N*2], args=(g,))

	stack = []
	for n in range(N):
		layer = Layer(name="[adjust gamma %d]" % n, value=r.x[n*2], mode="divide", opacity=r.x[n*2+1])
		stack.append(layer)

	return stack

def create_stack(b, g, w):

	# linear adjustment
	stack = [
		Layer("[adjust black]", b, "subtract", 1.),
		Layer("[adjust white]", w-b, "divide", 1.),
	]

	if g > 1.:
		stack += approx_gamma_poly(g)
	else:
		stack += approx_gamma_lin(g)

	return stack

#def main():
#	b = 0.2
#	w = 0.8
#	#g = 1.2
#	g = 0.3
#	stack = create_stack(b, w, g)
#
#	for layer in stack:
#		print repr(layer)
#
#if __name__ == "__main__":
#	main()

def fake_adj_layer(img, layer, b, g, w):
	stack = create_stack(float(b)/255, 1./g, float(w)/255)

	img.undo_group_start()

	for layer in stack:
		if layer.mode == 'subtract':
			m = 8
		elif layer.mode == 'divide':
			m = 15
		elif layer.mode == 'soft light':
			m = 19
		else:
			assert False

		lay = pdb.gimp_layer_new(img,
				img.width, img.height,
				0, # RGB
				layer.name,
				layer.opacity*100,
				m)

		img.insert_layer(lay)

		v =int(round((layer.value)*255.))
		if m == 15:
			v = v - 1

		pdb.gimp_context_set_foreground((v,v,v))
		pdb.gimp_edit_fill(lay, 0)

	img.undo_group_end()

register(
	"python_fu_fake_adjustment",
	"Create a fake adjustment layer",
	"Create a fake adjustment layer",
	"Tomaz Solc",
	"GPLv3+",
	"2017",
	"<Image>/Layer/Fake adjustment",
	"*",
	[
		(PF_INT, "b", "Black point", 0),
		(PF_FLOAT, "g", "Gamma", 1.),
		(PF_INT, "w", "White point", 255),
	],
	[],
	fake_adj_layer)

main()
