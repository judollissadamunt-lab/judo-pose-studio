import sys,json,tempfile,os,math,itertools
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(tempfile.mkdtemp(prefix='judo-visual-'));out.mkdir(parents=True,exist_ok=True)
def segment_distance(p,q,r,s):
 def sub(a,b):return [x-y for x,y in zip(a,b)]
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def point_segment(a,b,c):
  v=sub(c,b);w=sub(a,b);t=max(0,min(1,dot(w,v)/dot(v,v)))
  return math.dist(a,[x+t*y for x,y in zip(b,v)])
 u,v,w=sub(q,p),sub(s,r),sub(p,r)
 a,b,c,d,e=dot(u,u),dot(u,v),dot(v,v),dot(u,w),dot(v,w)
 distances=[point_segment(p,r,s),point_segment(q,r,s),point_segment(r,p,q),point_segment(s,p,q)]
 determinant=a*c-b*b
 if determinant>1e-12:
  t,h=(b*e-c*d)/determinant,(a*e-b*d)/determinant
  if 0<=t<=1 and 0<=h<=1:
   distances.append(math.dist([x+t*y for x,y in zip(p,u)],[x+h*y for x,y in zip(r,v)]))
 return min(distances)

with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  response=r.fetch();body=response.text().replace('</script></body>',"window.audit={people,scene,camera,controls,renderer,THREE,gripDestination,grips};</script></body>")
  r.fulfill(response=response,body=body)
 page.route('http://127.0.0.1:8000/',route)
 page.goto('http://127.0.0.1:8000/',wait_until='networkidle');page.wait_for_selector('canvas')
 page.locator('#classicGrip').click()
 for name,pos in [('frontal',[5,2,0]),('lateral',[0,2,5]),('superior',[0,6,.001])]:
  page.evaluate('(pos)=>{let a=window.audit;a.controls.enableDamping=false;a.controls.target.set(0,1.25,0);a.camera.position.set(...pos);a.controls.update();}',pos)
  page.wait_for_timeout(400);page.locator('#scene').screenshot(path=str(out/(name+'.png')))
 data=page.evaluate('''()=>{const {people,THREE,gripDestination,scene}=audit;scene.updateMatrixWorld(true);return Object.fromEntries(Object.entries(people).map(([id,p])=>[id,Object.fromEntries(['left','right'].map(side=>{let dest=gripDestination(id,side,side==='right'?'lapel':'sleeve',new THREE.Vector3());let wrist=p.joints[side+'Wrist'];let palm=wrist.localToWorld(new THREE.Vector3(0,-.095,0));return [side,{joints:Object.fromEntries(['Shoulder','Elbow','Wrist'].map(k=>[k,{position:p.joints[side+k].getWorldPosition(new THREE.Vector3()).toArray(),rotation:p.joints[side+k].rotation.toArray()}])),palm:palm.toArray(),target:dest.toArray(),gap:palm.distanceTo(dest)}]}))]));}''')
 (out/'metrics.json').write_text(json.dumps(data,indent=2));print(json.dumps(data))
 for person in data.values():
  for arm in person.values():
   assert arm['gap']<.005,arm
   r=arm['joints']['Elbow']['rotation'];assert -2.531<=r[0]<=0 and r[1:3]==[0,0]
   r=arm['joints']['Wrist']['rotation'];assert abs(r[0])<.22 and abs(r[1])<=.79 and r[2]==0
 # Guard against the previous forearm crossing in the initial preset.
 # This segment check supplements screenshots; it is not mesh collision detection.
 arms=[[a['joints'][key]['position'] for key in ['Shoulder','Elbow','Wrist']]
       for person in data.values() for a in person.values()]
 separation=min(segment_distance(a[i],a[i+1],b[j],b[j+1])
                for a,b in itertools.combinations(arms,2) for i in range(2) for j in range(2))
 assert separation>.245,separation
 print(f'PASS: minimum arm segment separation {separation:.3f}m (preset only)')
 # Idempotence, local anatomical sides, torso/head reset and UI hinge bounds.
 page.locator('#classicGrip').click()
 assert page.evaluate("()=>audit.people.tori.joints.leftShoulder.position.x>0 && audit.people.tori.joints.rightShoulder.position.x<0")
 page.select_option('#joint','rightElbow')
 assert page.locator('#rotY').is_disabled() and page.locator('#rotZ').is_disabled()
 page.locator('#rotX').fill('-100');page.locator('#rotX').dispatch_event('input')
 assert page.locator('#xVal').inner_text()=='-100°'
 page.locator('#classicGrip').click()
 initial=page.evaluate("()=>Object.fromEntries(Object.entries(audit.people).map(([id,p])=>[id,Object.fromEntries(Object.entries(p.joints).map(([k,j])=>[k,j.rotation.toArray().slice(0,3)]))]))")
 page.locator('#saveStep').click();page.locator('#newStep').click()
 page.select_option('#joint','rightElbow');page.locator('#rotX').fill('-90');page.locator('#rotX').dispatch_event('input');page.locator('#saveStep').click()
 page.locator('#playAnim').click();page.wait_for_function("document.querySelector('#progressText').textContent==='100%'",timeout=15000)
 page.locator('#prevStep').click()
 restored=page.evaluate("()=>Object.fromEntries(Object.entries(audit.people).map(([id,p])=>[id,Object.fromEntries(Object.entries(p.joints).map(([k,j])=>[k,j.rotation.toArray().slice(0,3)]))]))")
 assert initial==restored
 with page.expect_download() as d:page.locator('#exportJson').click()
 exported=Path(d.value.path()).read_bytes()
 page.locator('#importFile').set_input_files({'name':'roundtrip.json','mimeType':'application/json','buffer':exported})
 assert page.locator('#steps button').count()==2
 page.wait_for_timeout(1700);page.reload(wait_until='networkidle');page.wait_for_selector('canvas');assert page.locator('#steps button').count()==2
 print('PASS: four contacts <5mm, hinge/wrist limits, anatomical sides, editing, animation, exact phase restoration, JSON import/export, local persistence')
 assert not errors,errors
 b.close()
