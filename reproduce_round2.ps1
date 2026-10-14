$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$researchPython = Join-Path $PSScriptRoot '.venv-research\Scripts\python.exe'
function Run-Research([string[]]$Arguments) {
    & $researchPython @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Reproduction step failed: $Arguments" }
}
Run-Research @('-I','-B','tests/test_v2.py')
Run-Research @('-B','evaluate.py','--campaign','v2','--method-version','v1','--split','test','--mode','full_paper_ablation')
Run-Research @('-B','evaluate.py','--campaign','v2','--split','test','--mode','full_paper_ablation')
Run-Research @('-I','-B','paper/update_round2.py')
Run-Research @('-I','-B','paper/build.py')
Run-Research @('-I','-B','paper/build_zh.py')
