const {JSDOM}=require('jsdom');const fs=require('fs');const assert=require('assert');
const html=fs.readFileSync('src/lifecycle_mapper/ui/index.html','utf8');
const errors=[];const dom=new JSDOM(html,{runScripts:'dangerously',url:'http://127.0.0.1:8000',beforeParse(w){w.fetch=async()=>({ok:true,json:async()=>[]})}});
const w=dom.window,d=w.document;
const evidence={stage:'Collection',source:'documentation',path:'README.md',start_line:2,end_line:2,excerpt:'We collect raw research data.',url:'https://github.com/test/repo/blob/'+ 'a'.repeat(40)+'/README.md#L2-L2',rule_id:'COL_DOC',rule_version:'v1',evidence_id:'unique'};
const modes=['documentation-only','code-only','combined'].map(mode=>({mode,labels:mode==='code-only'?[]:['Collection'],evidence:mode==='code-only'?[]:[evidence],scan_complete:true}));
const result={repositories:[{repository:'test/repo',source_url:'https://github.com/test/repo',commit:'a'.repeat(40),modes,human_labels:{Collection:0,Processing:0,Method:0,Experimentation:0,Evaluation:0,Dissemination:0}},{repository:'test/failed',source_url:'https://github.com/test/failed',modes:[],error:'rate-limit'}]};
w.render({id:'test',result});
assert.equal(d.querySelectorAll('tr[data-repo]').length,2);assert.equal(d.querySelectorAll('.evidence').length,1);
assert(d.querySelector('#repo-detail').textContent.includes('Overall unique'));
assert(d.querySelector('#repo-detail').textContent.includes('Matched rules'));
d.querySelector('#review-mismatch').value='mismatch';w.overview();assert.equal(d.querySelectorAll('tr[data-repo]').length,1);
d.querySelector('#review-query').value='absent';w.overview();assert.equal(d.querySelectorAll('tr[data-repo]').length,0);
d.querySelector('#review-query').value='';d.querySelector('#review-mismatch').value='partial';w.overview();assert.equal(d.querySelectorAll('tr[data-repo]').length,1);w.detail(1);assert(d.querySelector('#repo-detail').textContent.includes('rate-limit'));
// Imported evidence must not become executable HTML or a javascript link.
result.repositories[0].modes[2].evidence[0].excerpt='<img src=x onerror=alert(1)>';
result.repositories[0].modes[2].evidence[0].url='javascript:alert(1)';w.detail(0);
assert.equal(d.querySelectorAll('#repo-detail img').length,0);assert.equal(d.querySelector('#repo-detail a').getAttribute('href'),'#');
console.log('DOM review checks passed: one row, mode deduplication, counts, reference mismatches, filters, partial failure detail, escaped excerpts, safe links.');dom.window.close();
