.PHONY: clean

clean:
	rm -rf ./log/* ./history/* ./output/*
	find ./rtl/ -type f -name "*.v" ! -name "*.v0.v" -delete
	find ./rtl/ -type f -name "*.sv" ! -name "*.v0.sv" -delete