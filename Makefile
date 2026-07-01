.PHONY: install run eval test
install:
	pip install -r requirements.txt
run:
	python -m graphrag "Por que o Cenario S1 exige aquecimento ativo?"
eval:
	python -m graphrag --eval data/questions.yaml
test:
	pytest -q
