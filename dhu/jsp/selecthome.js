$(function(){
	initCourses();
});

var termTmp = {'1A':1, '1B':2, '2A':3, '2B':4, '3A':5, '3B':6, '4A':7, '4B':8};
var getCreditsTmp = {};
var getCateCreditsTmp = {};
var creditReplacedData = {};// 学生抵充学分数据
var tgbInfoTbl;
var advancedTagId = 'accessClassTbl';
function initCourses() {
	$.ajax({
		url:contextPath+'/selectcourse/initTSCourses',
		type:'POST',
		dataType:'json',
		data:{'studNo':studNo, 'scSemester':scSemester, 'type': 'selectCourse'},
		success:function(result){
			if (result.success) {
				var eachPartTBody = '';
				var otherBasisPart = '<a style="margin-left:15px;" onclick="showOB()">选择其他专业的学科基础课</a>';
				var otherDirectionPart = '<a style="margin-left:15px;" onclick="showOD()">选择其他专业方向的课程</a>';
				var generalArtCrs = [];
				var generalArtCredits = 0;
				var courseDirections = {};
				if (result.tsCourses.bigSortKinds) {
					for (var i=0; i<result.tsCourses.bigSortKinds.length; i++) {
						var smallSort = '';
						var eachBigSortKind = result.tsCourses.bigSortKinds[i].split('-'); 
						getCreditsTmp[result.tsCourses.bigSortKinds[i]] = 0;
						eachPartTBody += '<tr class="fbold"><td>'+eachBigSortKind[0]+'</td><td colspan="'+(11+extendSemeCnt)+'"><span style="font-weight:bold" class="crKind">'+eachBigSortKind[1]+'</span><span style="color:red;margin-left:15px;">要求学分:<span class="askCredits">'+(result.tsCourses.tsCredits[result.tsCourses.bigSortKinds[i]]||'')+'</span></span><span style="color:red;margin-left:5px;">获得学分:<span class="getCredits"></span></span>'+('学科基础'==eachBigSortKind[0]&&'选修课'==eachBigSortKind[1]?otherBasisPart:'')+('专业方向'==eachBigSortKind[0]&&'选修课'==eachBigSortKind[1]?otherDirectionPart:'')+'</td></tr>';
						// 具体课程
						if (result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]]) {
							for (var j=0; j<result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]].length; j++) {
								// 显示课程小类标题
								if (!$.stringIsEmpty(result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].smallSort) 
										&& smallSort!=result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].smallSort
										&& '无'!=result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].smallSort) {
									smallSort = result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].smallSort;
									eachPartTBody += '<tr><td>'+eachBigSortKind[0]+'</td><td colspan="'+(11+extendSemeCnt)+'">'+result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].smallSort+'</td></tr>';
								}
								// 显示课程方向
								if (!$.stringIsEmpty(result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseDirection)
									&& (null==courseDirections[result.tsCourses.bigSortKinds[i]]||null==courseDirections[result.tsCourses.bigSortKinds[i]][result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseDirection])) {
									if (null==courseDirections[result.tsCourses.bigSortKinds[i]]) {
										courseDirections[result.tsCourses.bigSortKinds[i]] = {};
									}
									courseDirections[result.tsCourses.bigSortKinds[i]][result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseDirection] = result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseDirection;
									eachPartTBody += '<tr><td>'+eachBigSortKind[0]+'</td><td colspan="'+(11+extendSemeCnt)+'"><span class="crCateClass">'+result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseDirection+'</span></td></tr>';
								}
								// 显示课程
								eachPartTBody += '<tr><td>'+eachBigSortKind[0]+'</td>'+
													 '<td><a onclick="selectScope(this)">'+result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode+'</a></td>'+
													 '<td>'+result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseName+'</td>'+
													 '<td>'+(result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].credit?result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].credit.toFixed(1):'')+'</td>'+
													 parseYearTerm(result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode, 
															 		result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].yearTerm, 
															 		result.tsCourses.scgMap, 
															 		result.tsCourses.hadSelectCourseData,
														 			result.tsCourses.crScores)+
											     '</tr>';
								// 计算获得学分
								if (result.tsCourses.crScores[result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode]) {
									for (var it=0; it<result.tsCourses.crScores[result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode].length; it++) {
										if (null!=result.tsCourses.crScores[result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode][it][1]
											&& null!=result.tsCourses.crScores[result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode][it][2]
											&& 60<=parseFloat(result.tsCourses.crScores[result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode][it][1])) {
											getCreditsTmp[result.tsCourses.bigSortKinds[i]] += parseFloat(result.tsCourses.crScores[result.tsCourses.tsCourseMapNoCagegory[result.tsCourses.bigSortKinds[i]][j].courseCode][it][2]);
											break;
										}
									}
								}
							}
						}
						// 类别课程
						if (result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]]) {
							for (var j=0; j<result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]].length; j++) {
								var cateAskCredit = '';
								for (var cateKey in result.tsCourses.tsCredits) {
									if (-1< cateKey.indexOf(eachBigSortKind[0])
										&& -1< cateKey.indexOf(eachBigSortKind[1])
										&& -1<cateKey.indexOf(result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j])) {
										//console.log()
										cateAskCredit = '<span style="margin-left:15px;">要求学分:<span class="askCreditsCate">'+result.tsCourses.tsCredits[cateKey]+'</span></span><span style="margin-left:15px;">获得学分:<span class="getCreditsCate" bkcattr="'+(result.tsCourses.bigSortKinds[i]+'-'+result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j])+'" cateattr="'+result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]+'"></span></span>';
										if(result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]==='公共外语类'){
											cateAskCredit+='<span style="margin-left:15px;">(英语和日语平行计算，二者不能相互叠加)</span>'
										}
										break;
									}
								}
								eachPartTBody += '<tr><td>'+eachBigSortKind[0]+'</td><td colspan="'+(11+extendSemeCnt)+'"><a onclick="showCC(this)"><span class="crCate">'+result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]+'</span></a>'+cateAskCredit+'</td></tr>';
								
								if (result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]]) {
									for (var k=0; k<result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]].length; k++) {
										if ('2019'<=grade && '2025'>grade && !result.isArtMajor
											&& '文化素质类' == result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]
											&& ('艺术类'==result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].categoryDesc
												|| -1<(result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].categoryDesc||'').indexOf('艺术类'))) {
											generalArtCrs.push('<tr><td>'+eachBigSortKind[0]+'</td>'+
																'<td>'+result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode+'</td>'+
																'<td>'+result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseName+'</td>'+
																'<td>'+(result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].credit?result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].credit.toFixed(1):'')+'</td>'+
																parseYearTermCategory(result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode,
																	result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].yearTerm,
																	result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].score,
																	result.tsCourses.hadSelectCourseData,
																	result.tsCourses.crScores)+
																'</tr>');
											if (result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode]) {
												for (var artIdx=0; artIdx<result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode].length; artIdx++) {
													if (result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode][artIdx][1]
														&& 60<=parseFloat(result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode][artIdx][1])) {
														generalArtCredits += parseFloat(result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].credit);
														break;
													}
												}
											}
										} else {
											eachPartTBody += '<tr><td>'+eachBigSortKind[0]+'</td>'+
																 '<td>'+result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode+'</td>'+
																 '<td>'+result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseName+'</td>'+
																 '<td>'+(result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].credit?result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].credit.toFixed(1):'')+'</td>'+
																 parseYearTermCategory(result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode,
																						result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].yearTerm,
																						result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].score,
																						result.tsCourses.hadSelectCourseData,
																	 					result.tsCourses.crScores)+
															 '</tr>';
										}
										if (result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode]) {
											for (var it=0; it<result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode].length; it++) {
												if (null!=result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode][it][1]
													&& null!=result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode][it][2]
													&& 60<=parseFloat(result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode][it][1])) {
													getCreditsTmp[result.tsCourses.bigSortKinds[i]] += parseFloat(result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode][it][2]);
													if (!getCateCreditsTmp[result.tsCourses.bigSortKinds[i]+'-'+result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]]) {
														getCateCreditsTmp[result.tsCourses.bigSortKinds[i]+'-'+result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]] = 0;
													}
													getCateCreditsTmp[result.tsCourses.bigSortKinds[i]+'-'+result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]] += parseFloat(result.tsCourses.crScores[result.tsCourses.categorySCGMap[result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]][k].courseCode][it][2]);
													break;
												}
											}
										}
									}
								}

								if ('2019'<=grade && '2025'>grade && !result.isArtMajor
									&& '文化素质类' == result.tsCourses.tsCourseMapWidthCategory[result.tsCourses.bigSortKinds[i]][j]) {
									eachPartTBody += '<tr><td>'+eachBigSortKind[0]+'</td><td colspan="'+(11+extendSemeCnt)+'">文化素质类-艺术类<span style="color:'+(2<=generalArtCredits?'blue':'red')+';margin-left:15px;">要求学分:2</span><span style="color:'+(2<=generalArtCredits?'blue':'red')+';margin-left:5px;">获得学分:'+generalArtCredits+'</span></td></tr>';
									for (var it=0; it<generalArtCrs.length; it++) {
										eachPartTBody += generalArtCrs[it];
									}
								}
							}
						}
					}
				}
				$('#tsCoursesTbl tbody').html(eachPartTBody);

				// 设置学生抵充学分
				if (result.creditReplacedSet && 0<result.creditReplacedSet.length) {
					for (var i=0; i<result.creditReplacedSet.length; i++) {
						if (!creditReplacedData[result.creditReplacedSet[i]['KCDL']+'-'+result.creditReplacedSet[i]['KCXZ']]) {
							creditReplacedData[result.creditReplacedSet[i]['KCDL']+'-'+result.creditReplacedSet[i]['KCXZ']] = [];
						}
						creditReplacedData[result.creditReplacedSet[i]['KCDL']+'-'+result.creditReplacedSet[i]['KCXZ']].push(result.creditReplacedSet[i]);

						if (result.creditReplacedSet[i]['KCLB']) {
							if (!creditReplacedData[result.creditReplacedSet[i]['KCLB']]) {
								creditReplacedData[result.creditReplacedSet[i]['KCLB']] = [];
							}
							creditReplacedData[result.creditReplacedSet[i]['KCLB']].push(result.creditReplacedSet[i]);
						}
					}
				}
				
				setTimeout(function(){
					if (result.tsCourses.bigSortKinds) {
						for (var i=0; i<result.tsCourses.bigSortKinds.length; i++) {
							// 获取抵充学分
							var replaceCredit = 0;
							if (creditReplacedData[result.tsCourses.bigSortKinds[i]]) {
								for (var j=0; j<creditReplacedData[result.tsCourses.bigSortKinds[i]].length; j++) {
									replaceCredit += parseFloat(creditReplacedData[result.tsCourses.bigSortKinds[i]][j]['XF']||'0');
								}
							}
							$('.getCredits:eq('+i+')').html(getCreditsTmp[result.tsCourses.bigSortKinds[i]]+replaceCredit);
							if (!$.stringIsEmpty(getCreditsTmp[result.tsCourses.bigSortKinds[i]])
								&& !$.stringIsEmpty($('.getCredits:eq('+i+')').parent().parent().find('.askCredits').html())
								&& parseFloat($('.getCredits:eq('+i+')').parent().parent().find('.askCredits').html())<=(getCreditsTmp[result.tsCourses.bigSortKinds[i]]+replaceCredit)) {
								$('.getCredits:eq('+i+')').parent().css('color', 'blue');
								$('.getCredits:eq('+i+')').parent().prev().css('color', 'blue');
							}
						}
					}

					$('.getCreditsCate').each(function () {
						// 获取抵充学分
						var replaceCredit = 0;
						if (creditReplacedData[$(this).attr('cateattr')]) {
							for (var j=0; j<creditReplacedData[$(this).attr('cateattr')].length; j++) {
								replaceCredit += parseFloat(creditReplacedData[$(this).attr('cateattr')][j]['XF']||'0');
							}
						}
						if (getCateCreditsTmp[$(this).attr('bkcattr')] || replaceCredit) {
							$(this).html((getCateCreditsTmp[$(this).attr('bkcattr')]?getCateCreditsTmp[$(this).attr('bkcattr')]:0)+replaceCredit);
						} else {
							$(this).html(0);
						}
						var askCC = parseFloat($.stringIsEmpty($(this).parent().parent().find('.askCreditsCate').html())?'0':$(this).parent().parent().find('.askCreditsCate').html());
						var getCC = (getCateCreditsTmp[$(this).attr('bkcattr')]?getCateCreditsTmp[$(this).attr('bkcattr')]:0)+replaceCredit;
						if (askCC > getCC) {
							$(this).parent().parent().css('color', 'red');
						} else {
							$(this).parent().parent().css('color', 'blue');
						}
					});
				}, 50);
				var showDesc = result.showDesc;
				setTimeout(function () {
					var maxWidth = 0;
					$('.crCateClass').each(function () {
						//console.log($(this).css('width'));
						var eachWidth = parseInt(($(this).css('width')||'').replace('px',''));
						if (maxWidth < eachWidth) {
							maxWidth = eachWidth;
						}
					});
					if (null!=showDesc && 1==showDesc) {
						$('.crCateClass').each(function () {
							$(this).css('width', maxWidth+'px');
							$(this).css('display', 'inline-block');
							$(this).parent().append('<span style="color: red;margin-left: 10px;">各专业方向对应的模块课程为自己方向的限选课（即必修性质），为其他方向的选修课</span>');
						});
					}

					$('.crKind').each(function () {
						var kcdl = $(this).parent().prev().html();
						var kcxz = $(this).html();
						if (creditReplacedData[kcdl+'-'+kcxz]) {
							$(this).parent().append('<span class="showReplaced" kAttr="'+kcdl+'-'+kcxz+'">查看抵充</span>');
						}
					});
					$('.crCate').each(function () {
						var kclb = $(this).html();
						if (creditReplacedData[kclb]) {
							$(this).parent().parent().append('<span class="showReplaced" kAttr="'+kclb+'">查看抵充</span>');
						}
					});
					setTimeout(function () {
						$('.showReplaced').click(function () {
							$('#creditReplacedTbl tbody').empty();
							if (creditReplacedData[$(this).attr('kAttr')]) {
								for (var i=0; i<creditReplacedData[$(this).attr('kAttr')].length; i++) {
									$('#creditReplacedTbl tbody').append('<tr>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['LX']||'')+'</td>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['NME']||'')+'</td>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['KCDL']||'')+'</td>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['KCXZ']||'')+'</td>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['KCLB']||'')+'</td>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['KC']||'')+'</td>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['XF']||'')+'</td>' +
										'<td>'+(creditReplacedData[$(this).attr('kAttr')][i]['CJ']||'')+'</td>' +
										'</tr>');
								}
							}
							$('#creditReplacedFld').css('display', '');
						});
					},200);
				}, 300);
			} else {
				alert(result.msg);
			}

			initHonorCourses();
		},
		error:function(){
			alert('');
		}
	});
}

function initHonorCourses() {
	$.ajax({
		url:contextPath+'/selectcourse/initHonorCourses',
		type:'POST',
		dataType:'json',
		data:{'studNo':studNo, 'scSemester':scSemester},
		success:function(result){
			if (result.success) {
				$('#tsCoursesTbl tbody').append('<tr><td colspan="'+(12+extendSemeCnt)+'" style="border-left: 0px solid white;border-right: 0px solid white;"></td></tr>');
				for (var key in result.hornorCrs) {
					$('#tsCoursesTbl tbody').append('<tr class="fbold" style="color:red;"><td>荣誉课程</td><td colspan="'+(11+extendSemeCnt)+'">'+key+'</td></tr>');
					for (var it=0; it<result.hornorCrs[key].length; it++) {
						var honorTr = '<tr>' +
							'<td>荣誉课程</td>' +
							'<td><a onclick="selectScope(this)">'+result.hornorCrs[key][it].KCBH+'</a></td>' +
							'<td>'+result.hornorCrs[key][it].KCMC+'</td>' +
							'<td>'+parseFloat(result.hornorCrs[key][it].XF||0).toFixed(1)+'</td>' +
							parseYearTermHonor(result.hornorCrs[key][it].KCBH,
								result.hornorCrs[key][it].XQ,
								result.hornorCrs[key][it].XQH,
								result.hornorCrs[key][it].CJ) +
							'</tr>';
						$('#tsCoursesTbl tbody').append(honorTr);
					}
				}
			}
		},
		error:function(){}
	});
}

function parseYearTerm(courseCode, yearTerm, scgMap, hadSelectCourseData, crScores) {
	var showIdx = {};
	if (crScores && null!=crScores[courseCode]) {
		for (var it=0; it<crScores[courseCode].length; it++) {
			var yearTerm1 = crScores[courseCode][it][0]||'1A';
			var showTxt = '';
			if (4==crScores[courseCode][it].length && null!=crScores[courseCode][it][1]) {
				if (60 <= parseFloat(crScores[courseCode][it][1])) {
					showTxt = '<span style="color:blue;">'+parseFloat(crScores[courseCode][it][1]).toFixed(1)+'</span>';
				} else {
					showTxt = '<span style="color:red;">'+parseFloat(crScores[courseCode][it][1]).toFixed(1)+'</span>';
				}
			} else {
				if (scSemester == yearTerm1) {
					if (1==crScores[courseCode][it][3])
						showTxt = '<span style="color:red;">退课中</span>';
					else
						showTxt = '<span style="color:#00008b;">已选</span>';
				} else {
					showTxt = '在读';
				}
			}
			var tempIdx = (parseInt(yearTerm1.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(yearTerm1.indexOf('s')>-1?1:0);
			tempIdx = (1>tempIdx?1:tempIdx);
			showIdx[tempIdx]=showTxt;
		}
	} else {
		yearTerm = yearTerm||'1A';
		var showTxt = '未读';
		showIdx[termTmp[yearTerm]] = showTxt;
	}

	var result = '';
	var curIdx = (parseInt(scSemester.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(scSemester.indexOf('s')>-1?1:0);
	curIdx = (1>curIdx?1:curIdx);
	for (var i=1; i<=8+extendSemeCnt; i++) {
		if (null != showIdx[i]) {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'>'+showIdx[i]+'</td>';
		} else {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'></td>';
		}
	}
	return result;
}

function parseYearTermCategory(courseCode, yearTerm, score, hadSelectCourseData, crScores) {
	var showIdx = {};

	if (crScores && null!=crScores[courseCode]) {
		for (var it=0; it<crScores[courseCode].length; it++) {
			var yearTerm1 = crScores[courseCode][it][0]||'1A';
			var showTxt = '';
			if (4==crScores[courseCode][it].length && null!=crScores[courseCode][it][1]) {
				if (60 <= parseFloat(crScores[courseCode][it][1])) {
					showTxt = '<span style="color:blue;">'+parseFloat(crScores[courseCode][it][1]).toFixed(1)+'</span>';
				} else {
					showTxt = '<span style="color:red;">'+parseFloat(crScores[courseCode][it][1]).toFixed(1)+'</span>';
				}
			} else {
				if (scSemester == yearTerm1) {
					if (1==crScores[courseCode][it][3])
						showTxt = '<span style="color:red;">退课中</span>';
					else
						showTxt = '<span style="color:#00008b;">已选</span>';
				} else {
					showTxt = '在读';
				}
			}
			var tempIdx = (parseInt(yearTerm1.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(yearTerm1.indexOf('s')>-1?1:0);
			tempIdx = (1>tempIdx?1:tempIdx);
			showIdx[tempIdx] = showTxt;
		}
	} else {
		var showTxt = '未读';
		var tempIdx = (parseInt(yearTerm.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(yearTerm.indexOf('s')>-1?1:0);
		tempIdx = (1>tempIdx?1:tempIdx);
		showIdx[tempIdx] = showTxt;
	}

	var curIdx = (parseInt(scSemester.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(scSemester.indexOf('s')>-1?1:0);
	curIdx = (1>curIdx?1:curIdx);
	var result = '';
	for (var i=1; i<=8+extendSemeCnt; i++) {
		if (null != showIdx[i]) {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'>'+showIdx[i]+'</td>';
		} else {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'></td>';
		}
	}
	return result;
}

function parseYearTermHonor(courseCode, yearTerm, yearTermIdx, score) {
	var showTxt = '';
	if (yearTerm) {
		if (score) {
			if (60 <= parseFloat(score)) {
				showTxt = '<span style="color:blue;">'+parseFloat(score).toFixed(1)+'</span>';
			} else {
				showTxt = '<span style="color:red;">'+parseFloat(score).toFixed(1)+'</span>';
			}
		} else {
			if (scSemester == yearTerm) {
				showTxt = '<span style="color:#00008b;">已选</span>';
			} else {
				showTxt = '在读';
			}
		}
	} else {
		yearTerm = yearTerm||'1A';
		yearTermIdx = 1;
		var showTxt = '未读';
	}

	var result = '';
	var curIdx = (parseInt(scSemester.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(scSemester.indexOf('s')>-1?1:0);
	curIdx = (1>curIdx?1:curIdx);
	for (var i=1; i<=8+extendSemeCnt; i++) {
		if (i == yearTermIdx) {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'>'+showTxt+'</td>';
		} else {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'></td>';
		}
	}
	return result;
}

function parseYearTermBak(courseCode, yearTerm, scgMap, hadSelectCourseData) {
	yearTerm = yearTerm||'1A';
	var showTxt = '';
	var showIdx = 1;
	if (scgMap[courseCode] || 0==scgMap[courseCode]) {
		if (scgMap[courseCode].score) {
			if (60 <= scgMap[courseCode].score) {
				showTxt = '<span style="color:blue;">'+scgMap[courseCode].score.toFixed(1)+'</span>';
			} else {
				showTxt = '<span style="color:red;">'+scgMap[courseCode].score.toFixed(1)+'</span>';
			}
		} else {
			if (scSemester == scgMap[courseCode].yearTerm) {
				showTxt = '<span style="color:#00008b;">已选</span>';
			} else {
				showTxt = '在读';
			}
		}

		showIdx = (parseInt(scgMap[courseCode].yearTerm.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(scgMap[courseCode].yearTerm.indexOf('s')>-1?1:0);
		showIdx = (1>showIdx?1:showIdx);
	} else {
		showTxt = '未读';
		if (hadSelectCourseData) {
			for (var i=0; i<hadSelectCourseData.length; i++) {
				if (courseCode == hadSelectCourseData[i][0]) {
					showTxt = '<span style="color:#00008b;">已选</span>';
				}
			}
		}

		showIdx = termTmp[yearTerm];
	}

	var result = '';
	var curIdx = (parseInt(scSemester.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(scSemester.indexOf('s')>-1?1:0);
	curIdx = (1>curIdx?1:curIdx);
	for (var i=1; i<=8; i++) {
		if (showIdx == i) {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'>'+showTxt+'</td>';
		} else {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'></td>';
		}
	}
	return result;
}

function parseYearTermCategoryBak(courseCode, yearTerm, score, hadSelectCourseData) {
	var showTxt = '';
	if (score || 0==score) {
		if (60 <= score) {
			showTxt = '<span style="color:blue;">'+score.toFixed(1)+'</span>';
		} else {
			showTxt = '<span style="color:red;">'+score.toFixed(1)+'</span>';
		}
	} else {
		showTxt = '未读';
		if (hadSelectCourseData) {
			for (var i=0; i<hadSelectCourseData.length; i++) {
				if (courseCode == hadSelectCourseData[i][0]) {
					showTxt = '<span style="color:#00008b;">已选</span>';
				}
			}
		}
	}

	var showIdx = (parseInt(yearTerm.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(yearTerm.indexOf('s')>-1?1:0);
	var curIdx = (parseInt(scSemester.substring(0,4))-parseInt(grade.substring(0,4)))*2+1+(scSemester.indexOf('s')>-1?1:0);
	showIdx = (1>showIdx?1:showIdx);
	curIdx = (1>curIdx?1:curIdx);
	var result = '';
	for (var i=1; i<=8; i++) {
		if (showIdx == i) {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'>'+showTxt+'</td>';
		} else {
			result += '<td '+(i==curIdx?'style="background-color:#eaf1f1;"':'')+'></td>';
		}
	}
	return result;
}

function selectScope(aNode) {
	closeFailureMsg();
	$('#tsCoursesTbl tr.choseTr').removeClass('choseTr');
	$($(aNode).parents('tr')[0]).addClass('choseTr');
	$.ajax({
		url:contextPath+'/selectcourse/accessJudge',
		type:'POST',
		dataType:'json',
		data:{courseCode:$(aNode).html()},
		async:false,
		success:function(result){
			if (result.success) {
				if (result.warnings && 0<result.warnings.length) {
					$('#warnMsg').html('<i class="icon-warning-sign"></i>'+result.warnings.join('；'));
				} else {
					$('#warnMsg').html('');
				}
				openSCFld($(aNode).html());
				$('#opeCr').val($(aNode).html());
			} else {
				$('#failureMsg').html(result.msg);
				$('#failureMsgFld').css('display', '');
			}
		},
		error:function(){
			alert('');
		}
	});
}

function openSCFld(courseCode) {
	$('#accessClassTbl tbody').empty();
	$('#accessClassTbl').dataTable().fnDestroy();
	
	tgbInfoTbl = $('#accessClassTbl').dataTable({
        "bAutoWidth": false,
        "bPaginate":false,
        "bFilter": false,
        "bInfo": false,
        "bProcessing":false,
        "bServerSide": true,
        "sAjaxSource": contextPath+"/selectcourse/initACC",
        "fnServerParams": function (aoData) {
            aoData.push({"name": "courseCode", "value": courseCode});
        },
        "sServerMethod": "POST",
        "aoColumns": [{
            	'mData': 'cttId', 'bSortable': false, 'sWidth':'7%',
                'mRender': function (data, type, row) {    //列渲染
                	return '<span class="row-details row-details-close" style="display:none;"></span><a onclick="openSCC(this)">'+data+'</a>';
                }
	        }, {
	        	'mData': 'classNo', 'bSortable': false, 'sWidth':'7%'
	        }, {
	        	'mData': 'maxCnt', 'bSortable': false, 'sWidth':'10%'
        	}, {
        		'mData': 'applyCnt', 'bSortable': false, 'sWidth':'7%'
        	}, {
                'mData': 'enrollCnt', 'bSortable': false, 'sWidth':'7%'
        	}, {
        		'mData': 'priorMajors', 'bSortable': false, 'sWidth':'10%'
        	}, {
        		'mData': 'techName', 'bSortable': false, 'sWidth':'7%',  
        		'mRender': function(data, type, row) {
					var cttId = row.cttId;
//        			return '<a onclick="showTeacherInfo(this)" onmouseout="hideTeacherInfo(this)" style="text-decoration:none;">'+data+'</a>';
					if (row.pd==1){
						return '<a onclick="showTeacherInfo(this)" style="text-decoration:none;">'+data+'</a></br><a onclick="ckjxtd('+cttId+')" style="text-decoration:none;">查看教学团队</a>';
					} else {
						return '<a onclick="showTeacherInfo(this)" style="text-decoration:none;">'+data+'</a>';

					}
        		}
        	}, {
        		'mData': 'cttId', 'bSortable': false, 'sWidth':'15%',
                'mRender': function (data, type, row) {    //列渲染
                	var useWeekHtml = '';
                	var useWeekHtml1 = [];
                	var useWeekHtml2 = [];
                	if (!$.stringIsEmpty(row.useWeek1)) {
                		useWeekHtml1.push('<div style="width:100%;text-align:center;');
                		useWeekHtml2.push('">'+row.useWeek1+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek2)) {
                		useWeekHtml1.push('<div style="width:100%;text-align:center;');
                		useWeekHtml2.push('">'+row.useWeek2+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek3)) {
                		useWeekHtml1.push('<div style="width:100%;text-align:center;');
                		useWeekHtml2.push('">'+row.useWeek3+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek4)) {
                		useWeekHtml1.push('<div style="width:100%;text-align:center;');
                		useWeekHtml2.push('">'+row.useWeek4+'</div>');
                	}
                	if (1 == useWeekHtml1.length) {
                		useWeekHtml = useWeekHtml1[0]+useWeekHtml2[0];
                	} else if (1 < useWeekHtml1.length) {
                		for (var i=0; i<useWeekHtml1.length; i++) {
                			if (i != useWeekHtml1.length-1) {
                				useWeekHtml += useWeekHtml1[i]+'border-bottom:1px solid black;'+useWeekHtml2[i];
                			} else {
                				useWeekHtml += useWeekHtml1[i]+useWeekHtml2[i];
                			}
                		}
                	}
                	return useWeekHtml;
                }
            }, {
                'mData': 'cttId', 'bSortable': false, 'sWidth':'15%',
                'mRender': function (data, type, row) {    //列渲染
                	var classTimeHtml = '';
                	var classTimeHtml1 = [];
                	var classTimeHtml2 = [];
                	if (!$.stringIsEmpty(row.useWeek1)) {
                		classTimeHtml1.push('<div style="width:100%;text-align:center;');
                		classTimeHtml2.push('">'+row.classTime1+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek2)) {
                		classTimeHtml1.push('<div style="width:100%;text-align:center;');
                		classTimeHtml2.push('">'+row.classTime2+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek3)) {
                		classTimeHtml1.push('<div style="width:100%;text-align:center;');
                		classTimeHtml2.push('">'+row.classTime3+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek4)) {
                		classTimeHtml1.push('<div style="width:100%;text-align:center;');
                		classTimeHtml2.push('">'+row.classTime4+'</div>');
                	}
                	if (1 == classTimeHtml1.length) {
                		classTimeHtml = classTimeHtml1[0]+classTimeHtml2[0];
                	} else if (1 < classTimeHtml1.length) {
                		for (var i=0; i<classTimeHtml1.length; i++) {
                			if (i != classTimeHtml1.length-1) {
                				classTimeHtml += classTimeHtml1[i]+'border-bottom:1px solid black;'+classTimeHtml2[i];
                			} else {
                				classTimeHtml += classTimeHtml1[i]+classTimeHtml2[i];
                			}
                		}
                	}
                	return classTimeHtml;
                }
            }, {
            	'mData': 'cttId', 'bSortable': false, 'sWidth':'15%',
                'mRender': function (data, type, row) {    //列渲染
                	var roomCodeHtml = '';
                	var roomCodeHtml1 = [];
                	var roomCodeHtml2 = [];
                	if (!$.stringIsEmpty(row.useWeek1)) {
                		roomCodeHtml1.push('<div style="width:100%;text-align:center;');
                		roomCodeHtml2.push('">'+row.roomcode1+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek2)) {
                		roomCodeHtml1.push('<div style="width:100%;text-align:center;');
                		roomCodeHtml2.push('">'+row.roomcode2+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek3)) {
                		roomCodeHtml1.push('<div style="width:100%;text-align:center;');
                		roomCodeHtml2.push('">'+row.roomcode3+'</div>');
                	}
                	if (!$.stringIsEmpty(row.useWeek4)) {
                		roomCodeHtml1.push('<div style="width:100%;text-align:center;');
                		roomCodeHtml2.push('">'+row.roomcode4+'</div>');
                	}
                	if (1 == roomCodeHtml1.length) {
                		roomCodeHtml = roomCodeHtml1[0]+roomCodeHtml2[0];
                	} else if (1 < roomCodeHtml1.length) {
                		for (var i=0; i<roomCodeHtml1.length; i++) {
                			if (i != roomCodeHtml1.length-1) {
                				roomCodeHtml += roomCodeHtml1[i]+'border-bottom:1px solid black;'+roomCodeHtml2[i];
                			} else {
                				roomCodeHtml += roomCodeHtml1[i]+roomCodeHtml2[i];
                			}
                		}
                	}
                	return roomCodeHtml;
                }
            }
        ],
        "fnDrawCallback": function (oSettings) {
        	$('#curCourseName').html(oSettings.jqXHR.responseJSON.curCourse.kcmc);
			$('#curCourseCode').html(oSettings.jqXHR.responseJSON.curCourse.kcbh);
			$('#accessClassCnt').html(oSettings.jqXHR.responseJSON.aaData.length);
        	TableAdvanced.init();
        	showDoSCFld();
        	setTimeout(function(){
        		$.formatRadioAndCheckbox();
        	}, 1000);
        }
    });
}


function ckjxtd(jxbdm) {
	 
	$("#teateaminfo").find("tbody").html("")
	 
	$.ajax({
		url : contextPath+'/TeacherCourseTable/QueryTeachTeam',
		type : 'post',
		dataType : 'json',
		data:{jxbdm:jxbdm},
		success : function(result){
			if(result.success){
				if(result.list != null && result.list.length > 0){
					 
					var str = "";
					for(var i=0; i<result.list.length; i++){
						str += "<tr>";
						str += "<td>"+(result.list[i]['PKXX_ID']==null?"":result.list[i]['PKXX_ID'])+"</td>";
						str += "<td>"+(result.list[i]['XM']==null?"":result.list[i]['XM'])+"</td>";
						// str += "<td>"+(result.list[i]['GH']==null?"":result.list[i]['GH'])+"</td>";
						str += "<td>"+(result.list[i]['WORKLOAD']==null?"":result.list[i]['WORKLOAD'])+"</td>";
						// if ((result.list[i]['PD']==1)){
						//     str += "<td>"+(result.list[i]['XM']==null?"":result.list[i]['XM'])+"<a href=\"javascript:ckjxtd('"+(result.list[i]['ID']==null?"":result.list[i]['ID'])+"');\">  查看教学团队</a></td>";
						// }else {
						//     str += "<td>"+(result.list[i]['XM']==null?"":result.list[i]['XM'])+"</td>";
						// }

						str += "</tr>";
					}
					$("#teateaminfo").find("tbody").append(str);
				}
				$("#TeachTeamDlg").modal("show")
			}else {
				$('#publicprompt p').html("获取失败!" + result.msg);
				/* 屏蔽model以外内容的点击事件 */
				$('#publicprompt').modal({backdrop: 'static', keyboard: false});
			}
		},
		error:function(){
			$("#content").html("");
			$('#publicprompt p').html("获取失败!");
			/* 屏蔽model以外内容的点击事件 */
			$('#publicprompt').modal({backdrop: 'static', keyboard: false});
		}
	});
}
function showCC(aNode) {
	$('#smallSort').val($(aNode).find('span').html());
	$('#toCommonFrm').submit();
}

function showOB() {
	$('#oeBigSort').val('学科基础');
	$('#toOthersFrm').submit();
}
function showOD() {
	$('#oeBigSort').val('专业方向');
	$('#toOthersFrm').submit();
}

function seeSelected() {
//	window.open(contextPath+'/selectcourse/toSSC', '_blank');
	window.location.href=contextPath+'/selectcourse/toSSC';
}

function selectByOrgn() {
//	window.open(contextPath+'/selectcourse/toSelectByOrgn', '_blank');
	window.location.href=contextPath+'/selectcourse/toSelectByOrgn';
}

var scmList = [];
function showScmTbl() {
	if ($('#sidebar').css('display') == 'block') {
		$('#sidebar').css('display', 'none');
		return false;
	} else {
		$('#sidebar').css('display', '');
	}
	$('#scmList').empty();
	if (0 == scmList.length) {
		$.ajax({
			url:contextPath+'/scm/scmData',
			type:'POST',
			dataType:'json',
			data:{iDisplayStart:0, iDisplayLength:10},
			async:false,
			success:function(result){
				if (result.success) {
					for (var i=0; i<result.aaData.length; i++) {
						scmList.push(result.aaData[i]);
					}
				} else {
				}
			},
			error:function(){
			}
		});
	}
	if ($.isIE()) {
		for (var i=0; i<scmList.length; i++) {
			$('#scmList').append('<div class="btn-group" style="margin-bottom: 0px !important;">' +
				'<span class="btn blue" style="cursor: default;">'+scmList[i].nj.itemName+'级</span>' +
				'<a class="btn" style="background-color: #c3c3c3;color: red;font-weight: bold;" href="'+contextPath+'/scm/showSCM/'+scmList[i].id+'">'+scmList[i].manualName+'</a>' +
				'</div>');
		}
	} else {
		for (var i=0; i<scmList.length; i++) {
			$('#scmList').append('<div class="btn-group" style="margin-bottom: 0px !important;">' +
				'<span class="btn blue" style="cursor: default;">'+scmList[i].nj.itemName+'级</span>' +
				'<a class="btn" style="background-color: #c3c3c3;color: red;font-weight: bold;" onclick="showSCM(this,'+scmList[i].id+')">'+scmList[i].manualName+'</a>' +
				'</div>');
		}
	}
}

function showSCM(aNode, scmId) {
	$('#scmName').html($(aNode).text());
	// $('#scmContent').append('src', contextPath+'/scm/showSCM/online/'+scmId);
	$('#scmContent').remove();
	$('#showSCMField').append('<iframe id="scmContent" frameborder="0" style="width: 100%;height: 92%" src="'+contextPath+'/scm/showSCM/online/'+scmId+'"></iframe>');
	$('#showSCMField').modal('show');
}

function openSCC(aNode) {
	$('.row-details-open').each(function(){
		$(this).click();
	});
	
	if (($(aNode).parent().find('.row-details').attr('class')+'').indexOf('row-details-close')>-1) {
		$(aNode).parent().find('.row-details').click();
	}
}
function closeSCC(tdNode) {
	var $opeTr = $($(tdNode).parents('td.details')[0]).parent().prev('tr');
	if (($opeTr.find('.row-details').attr('class')+'').indexOf('row-details-open')>-1) {
		$opeTr.find('.row-details').click();
	}
}

function selectSubmit(aNode, cttId) {
	$.ajax({
		url:contextPath+'/selectcourse/scConflictCheck',
		type:'POST',
		dataType:'json',
		data:{'cttId':cttId},
		success:function(result){
			if (result.success) {
				doSelectSubmit(aNode, cttId);
			} else {
				// confirm(result.msg)
				if (confirm(result.msg+'\r\r选课有冲突，请确认是否继续提交')) {
					doSelectSubmit(aNode, cttId);
				}
			}
		},
		error:function(){
			alert('选课提交失败');
		}
	});
}
function doSelectSubmit(aNode, cttId) {
	var needMaterial = $($(aNode).parents('table')[0]).find('input[name="buyMaterial"]').prop('checked');
	var onclickAttr = $(aNode).attr('onclick');
	var capCode = $(aNode).parent().find('.capvalid .capCode').val();
	$.ajax({
		url:contextPath+'/selectcourse/scSubmit',
		type:'POST',
		dataType:'json',
		data:{'cttId':cttId, 'needMaterial':needMaterial, 'capCode':capCode},
		success:function(result){
			if (result.success) {
				if ('F' == result.msg) {
					refreshCaptcha(aNode, 1, result.capType);
				} else {
					alert('选课成功！');
					closeDoSCFld();
					initCourses();
					refreshCaptcha(aNode, 2);
				}
			} else {
				openSCFld($('#opeCr').val());
				if (result.msg && 0<result.msg.length) {
					alert(Array.isArray(result.msg)?result.msg.join('\r'):result.msg);
				} else if (result.warnMsg && result.warnMsg.length) {
					alert(result.warnMsg.join('\r'));
				} else {
					alert('选课提交失败，请刷新页面重试！');
				}
			}
			setTimeout(function () {
				$(aNode).attr('onclick', onclickAttr);
			}, 500);
		},
		error:function(){
			alert('');
		}
	});
}

function refreshCaptcha(aNode, type, capType) {
	if (1 == type) {
		$(aNode).parent().find('.capvalid').remove();
		$(aNode).before('<td rowspan="2" class="capvalid"><input type="text" class="capCode" style="width:60px;margin-right:10px;"><img src="'+contextPath+'/captcha/code" onclick="refreshCapImg(this)"></td>');
	} else if (2 == type) {
		$(aNode).parent().find('.capvalid').remove();
	}
}

function refreshCapImg(aNode) {
	$(aNode).attr('src', contextPath+'/captcha/code');
}

function showTeacherInfoBak(aNode) {
	$(aNode).popover('destroy');
	var $trNode = $(aNode).parents('tr')[0];
	var $trData = tgbInfoTbl.fnGetData($trNode);
	$(aNode).popover({
		placement:'right',
		html:true,
		content:function(){
			return  "<table id='techInfo' style='border:1px solid #ddd;'>"+"<tr><td><nobr>教师姓名:</nobr></td><td><nobr>"+$.stringDefault($trData['techName'],'') + "</nobr></td></tr>"+
								"<tr><td><nobr>性别:</nobr></td><td><nobr>"+$.stringDefault($trData['sex'],'') + "</nobr></td></tr>"+
								"<tr><td><nobr>职称:</nobr></td><td><nobr>"+$.stringDefault($trData['technicalTitle'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>电话号码（O）:</nobr></td><td><nobr>"+$.stringDefault($trData['phone'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>办公室地址:</nobr></td><td><nobr>"+$.stringDefault($trData['office'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>E-Mail地址:</nobr></td><td><nobr>"+$.stringDefault($trData['email'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>个人主页:</nobr></td><td><nobr>"+$.stringDefault($trData['homepage'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>学术社团及任职:</nobr></td><td><nobr>"+$.stringDefault($trData['extend1'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>给学生的话:</nobr></td><td><nobr>"+$.stringDefault($trData['extend2'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>近三年教学奖励:</nobr></td><td><nobr>"+$.stringDefault($trData['extend3'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>近三年教学经历:</nobr></td><td><nobr>"+$.stringDefault($trData['extend4'],'') +"</nobr></td></tr>"+
								"<tr><td><nobr>本学期教学说明:</nobr></td><td><nobr>"+$.stringDefault($trData['extend5'],'')+"</nobr></td></tr></table>";
		}
	});
	$(aNode).popover('show');
}

function showTeacherInfo(aNode) {
	$(aNode).popover('destroy');
	var $trNode = $(aNode).parents('tr')[0];
	var $trData = tgbInfoTbl.fnGetData($trNode);
	$('#techCol1').html($.stringDefault($trData['techName'],''));
	$('#techCol2').html($.stringDefault($trData['sex'],''));
	$('#techCol3').html($.stringDefault($trData['technicalTitle'],''));
	$('#techCol4').html($.stringDefault($trData['phone'],''));
	$('#techCol5').html($.stringDefault($trData['office'],''));
	$('#techCol6').html($.stringDefault($trData['email'],''));
	$('#techCol7').html($.stringDefault($trData['homepage'],''));
	$('#techCol8').html($.stringDefault($trData['extend1'],''));
	$('#techCol9').html($.stringDefault($trData['extend2'],''));
	$('#techCol10').html($.stringDefault($trData['extend3'],''));
	$('#techCol11').html($.stringDefault($trData['extend4'],''));
	$('#techCol12').html($.stringDefault($trData['extend5'],''));
	$('#teachInfoFld').modal({backdrop:'static', keybord:false});
}

function closeTechFld() {
	$('#teachInfoFld').modal('hide');
}

function hideTeacherInfo(aNode) {
	$(aNode).popover('destroy');
}

function closeFailureMsg() {
	$('#failureMsgFld').css('display', 'none');
}
function showDoSCFld() {
	$('#doSCFld').css('display', '');
}
function closeDoSCFld() {
	$('#doSCFld').css('display', 'none');
}
function showNotice() {
	$('#noticeFld').css('display', '');
}
function closeNotice() {
	$('#noticeFld').css('display', 'none');
}

function closeCreditReplaced() {
	$('#creditReplacedFld').css('display', 'none');
}