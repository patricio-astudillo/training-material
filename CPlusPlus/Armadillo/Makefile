CXX = g++
CPPFLAGS =
CXXFLAGS = -O2 -g -std=c++14 -Wall
LDFLAGS =
LIBS = -larmadillo -lm

.PRECIOUS: %.o

APPL = matrix_product.exe read_matrix.exe matrix_vector_product.exe \
       svd.exe elementwise.exe inverse.exe

all: $(APPL)

%.exe: %.o
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -o $@ $^ $(LDFLAGS) $(LIBS)

%.o: %.c
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<

clean:
	rm -f *.o $(APPL)
