var enrollTeacherInfos = [];
var selectedTeacherInfos = [];
$(function(){
	initCourses();
	$('#bbtn').attr('onclick', 'toSCHome()');
	
	$('#onlineView').on('hide', function () {
        $('#onlineView .content').html("");
    });

	$('#closeCCFld').on('click', function () {
		$('#courseConflictFld').css('display', 'none')
	});
});

function initCourses() {
	var showCrConflict = false;
	$.ajax({
		url:contextPath+'/selectcourse/initSelCourses',
		type:'POST',
		dataType:'json',
		success:function(result){
			if (result.success) {
				$('#enrollCnt').html(result.enrollCourses.length);
				$('#enrollCredits').html(result.credits[0]);
				$('#fstSelCnt').html(result.selectedCourses.length);
				$('#fstCredits').html(result.credits[1]);
				if (result.sct && '0'!=result.sct.selectCourseStatus) {
					$('.crCalendar').each(function(){
						$(this).after('<th class="crDel">删除</th>');
					});
				} else {
					$('.crDel').remove();
				}
				var enrollCrHtml = '';
				var selectedCrHtml = '';
				for (var i=0; i<result.enrollCourses.length; i++) {
					var useWeekHtml = '';
					var classTimeHtml = '';
					var roomCodeHtml = '';
					var useWeekHtml1 = [];
					var useWeekHtml2 = [];
					var classTimeHtml1 = [];
					var classTimeHtml2 = [];
					var roomCodeHtml1 = [];
					var roomCodeHtml2 = [];
					if (!$.stringIsEmpty(result.enrollCourses[i].useWeek1)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
                		useWeekHtml2.push('">'+result.enrollCourses[i].useWeek1+'</div>');
                		classTimeHtml1.push('<div style="width:100%;text-align:center;');
                		classTimeHtml2.push('">'+result.enrollCourses[i].classTime1+'</div>');
                		roomCodeHtml1.push('<div style="width:100%;text-align:center;');
                		roomCodeHtml2.push('">'+result.enrollCourses[i].classRoom1+'</div>');
					}
					if (!$.stringIsEmpty(result.enrollCourses[i].useWeek2)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
						useWeekHtml2.push('">'+result.enrollCourses[i].useWeek2+'</div>');
						classTimeHtml1.push('<div style="width:100%;text-align:center;');
						classTimeHtml2.push('">'+result.enrollCourses[i].classTime2+'</div>');
						roomCodeHtml1.push('<div style="width:100%;text-align:center;');
						roomCodeHtml2.push('">'+result.enrollCourses[i].classRoom2+'</div>');
					}
					if (!$.stringIsEmpty(result.enrollCourses[i].useWeek3)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
						useWeekHtml2.push('">'+result.enrollCourses[i].useWeek3+'</div>');
						classTimeHtml1.push('<div style="width:100%;text-align:center;');
						classTimeHtml2.push('">'+result.enrollCourses[i].classTime3+'</div>');
						roomCodeHtml1.push('<div style="width:100%;text-align:center;');
						roomCodeHtml2.push('">'+result.enrollCourses[i].classRoom3+'</div>');
					}
					if (!$.stringIsEmpty(result.enrollCourses[i].useWeek4)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
						useWeekHtml2.push('">'+result.enrollCourses[i].useWeek4+'</div>');
						classTimeHtml1.push('<div style="width:100%;text-align:center;');
						classTimeHtml2.push('">'+result.enrollCourses[i].classTime4+'</div>');
						roomCodeHtml1.push('<div style="width:100%;text-align:center;');
						roomCodeHtml2.push('">'+result.enrollCourses[i].classRoom4+'</div>');
					}
					if (1 == useWeekHtml1.length) {
						useWeekHtml = useWeekHtml1[0]+useWeekHtml2[0];
						classTimeHtml = classTimeHtml1[0]+classTimeHtml2[0];
						roomCodeHtml = roomCodeHtml1[0]+roomCodeHtml2[0];
					} else {
						for (var it=0; it<useWeekHtml1.length; it++) {
                			if (it != useWeekHtml1.length-1) {
                				useWeekHtml += useWeekHtml1[it]+'border-bottom:1px solid black;'+useWeekHtml2[it];
                			} else {
                				useWeekHtml += useWeekHtml1[it]+useWeekHtml2[it];
                			}
                		}
						for (var it=0; it<classTimeHtml1.length; it++) {
                			if (it != classTimeHtml1.length-1) {
                				classTimeHtml += classTimeHtml1[it]+'border-bottom:1px solid black;'+classTimeHtml2[it];
                			} else {
                				classTimeHtml += classTimeHtml1[it]+classTimeHtml2[it];
                			}
                		}
						for (var it=0; it<roomCodeHtml1.length; it++) {
                			if (it != roomCodeHtml1.length-1) {
                				roomCodeHtml += roomCodeHtml1[it]+'border-bottom:1px solid black;'+roomCodeHtml2[it];
                			} else {
                				roomCodeHtml += roomCodeHtml1[it]+roomCodeHtml2[it];
                			}
                		}
					}
					enrollTeacherInfos.push({'techName':result.enrollCourses[i].teachName,'technicalTitle':result.enrollCourses[i].technicalTitle,
											 'phone':result.enrollCourses[i].phone,'office':result.enrollCourses[i].office,
											 'email':result.enrollCourses[i].email,'homepage':result.enrollCourses[i].homepage,
											 'extend1':result.enrollCourses[i].extend1,'extend2':result.enrollCourses[i].extend2,
											 'extend3':result.enrollCourses[i].extend3,'extend4':result.enrollCourses[i].extend4,
											 'extend5':result.enrollCourses[i].extend5});
					debugger
					var EditStr="";
					if (result.enrollCourses[i].pd==1){
						EditStr='<td><a onclick="showTeacherInfo(this,1)">'+result.enrollCourses[i].teachName+'</a><a onclick="ckjxtd('+result.enrollCourses[i].jxbdm+')">  查看教学团队</a></td>'
					}else {
						EditStr='<td><a onclick="showTeacherInfo(this,1)">'+result.enrollCourses[i].teachName+'</a></td>'
					}
					enrollCrHtml += '<tr>'+
										'<td>'+result.enrollCourses[i].courseCode+'</td>'+
										'<td><a onclick="showCourseProp(\''+result.enrollCourses[i].courseCode+'\',1)">'+result.enrollCourses[i].courseName+'</a></td>'+
										'<td>'+result.enrollCourses[i].credit+'</td>'+
										'<td>'+result.enrollCourses[i].catetory+'</td>'+
										'<td>'+result.enrollCourses[i].classNo+'</td>'+
										'<td><a onclick="showCourseProp(\''+result.enrollCourses[i].courseCode+'\',2)">教学日历</a></td>'+
										// ((result.sct&&'0'!=result.sct.selectCourseStatus&&1==result.enrollCourses[i].allowSC)?(result.enrollCourses[i].delStatus=='1'?('<td><span style="color: red;">退课中</span></td>'):('<td><a onclick="cancelSC(this,1)">'+'删除'+'</a></td>')):'<td></td>')+
										((result.sct&&'0'!=result.sct.selectCourseStatus&&1==result.enrollCourses[i].allowSC)?(result.enrollCourses[i].delStatus=='1'?('<td><a onclick="cancelSC(this,1)">'+'删除'+'</a></td>'):('<td><a onclick="cancelSC(this,1)">'+'删除'+'</a></td>')):((result.sct&&'0'!=result.sct.selectCourseStatus)?'<td></td>':''))+
										// '<td><a onclick="showTeacherInfo(this,1)">'+result.enrollCourses[i].teachName+'</a></td>'+
										''+EditStr+''+
										'<td style="'+(result.enrollCourses[i].conflict?'color:red;':'')+'">'+useWeekHtml+(result.enrollCourses[i].conflict?'<i class="icon-warning-sign crconflict"></i>':'')+'</td>'+
										'<td style="'+(result.enrollCourses[i].conflict?'color:red;':'')+'">'+classTimeHtml+(result.enrollCourses[i].conflict?'<i class="icon-warning-sign crconflict"></i>':'')+'</td>'+
										'<td>'+roomCodeHtml+'</td>'+
									'</tr>';
					if (result.enrollCourses[i].conflict) {
						showCrConflict = true;
					}
				}
				$('#enrollCoursesTbl tbody').html(enrollCrHtml);
				for (var i=0; i<result.selectedCourses.length; i++) {
					var useWeekHtml = '';
					var classTimeHtml = '';
					var roomCodeHtml = '';
					var useWeekHtml1 = [];
					var useWeekHtml2 = [];
					var classTimeHtml1 = [];
					var classTimeHtml2 = [];
					var roomCodeHtml1 = [];
					var roomCodeHtml2 = [];
					if (!$.stringIsEmpty(result.selectedCourses[i].useWeek1)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
						useWeekHtml2.push('">'+result.selectedCourses[i].useWeek1+'</div>');
						classTimeHtml1.push('<div style="width:100%;text-align:center;');
						classTimeHtml2.push('">'+result.selectedCourses[i].classTime1+'</div>');
						roomCodeHtml1.push('<div style="width:100%;text-align:center;');
						roomCodeHtml2.push('">'+result.selectedCourses[i].classRoom1+'</div>');
					}
					if (!$.stringIsEmpty(result.selectedCourses[i].useWeek2)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
						useWeekHtml2.push('">'+result.selectedCourses[i].useWeek2+'</div>');
						classTimeHtml1.push('<div style="width:100%;text-align:center;');
						classTimeHtml2.push('">'+result.selectedCourses[i].classTime2+'</div>');
						roomCodeHtml1.push('<div style="width:100%;text-align:center;');
						roomCodeHtml2.push('">'+result.selectedCourses[i].classRoom2+'</div>');
					}
					if (!$.stringIsEmpty(result.selectedCourses[i].useWeek3)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
						useWeekHtml2.push('">'+result.selectedCourses[i].useWeek3+'</div>');
						classTimeHtml1.push('<div style="width:100%;text-align:center;');
						classTimeHtml2.push('">'+result.selectedCourses[i].classTime3+'</div>');
						roomCodeHtml1.push('<div style="width:100%;text-align:center;');
						roomCodeHtml2.push('">'+result.selectedCourses[i].classRoom3+'</div>');
					}
					if (!$.stringIsEmpty(result.selectedCourses[i].useWeek4)) {
						useWeekHtml1.push('<div style="width:100%;text-align:center;');
						useWeekHtml2.push('">'+result.selectedCourses[i].useWeek4+'</div>');
						classTimeHtml1.push('<div style="width:100%;text-align:center;');
						classTimeHtml2.push('">'+result.selectedCourses[i].classTime4+'</div>');
						roomCodeHtml1.push('<div style="width:100%;text-align:center;');
						roomCodeHtml2.push('">'+result.selectedCourses[i].classRoom4+'</div>');
					}
					if (1 == useWeekHtml1.length) {
						useWeekHtml = useWeekHtml1[0]+useWeekHtml2[0];
						classTimeHtml = classTimeHtml1[0]+classTimeHtml2[0];
						roomCodeHtml = roomCodeHtml1[0]+roomCodeHtml2[0];
					} else {
						for (var it=0; it<useWeekHtml1.length; it++) {
							if (it != useWeekHtml1.length-1) {
								useWeekHtml += useWeekHtml1[it]+'border-bottom:1px solid black;'+useWeekHtml2[it];
							} else {
								useWeekHtml += useWeekHtml1[it]+useWeekHtml2[it];
							}
						}
						for (var it=0; it<classTimeHtml1.length; it++) {
							if (it != classTimeHtml1.length-1) {
								classTimeHtml += classTimeHtml1[it]+'border-bottom:1px solid black;'+classTimeHtml2[it];
							} else {
								classTimeHtml += classTimeHtml1[it]+classTimeHtml2[it];
							}
						}
						for (var it=0; it<roomCodeHtml1.length; it++) {
							if (it != roomCodeHtml1.length-1) {
								roomCodeHtml += roomCodeHtml1[it]+'border-bottom:1px solid black;'+roomCodeHtml2[it];
							} else {
								roomCodeHtml += roomCodeHtml1[it]+roomCodeHtml2[it];
							}
						}
					}
					selectedTeacherInfos.push({'techName':result.selectedCourses[i].teachName,'technicalTitle':result.selectedCourses[i].technicalTitle,
											   'phone':result.selectedCourses[i].phone,'office':result.selectedCourses[i].office,
											   'email':result.selectedCourses[i].email,'homepage':result.selectedCourses[i].homepage,
											   'extend1':result.selectedCourses[i].extend1,'extend2':result.selectedCourses[i].extend2,
											   'extend3':result.selectedCourses[i].extend3,'extend4':result.selectedCourses[i].extend4,
											   'extend5':result.selectedCourses[i].extend5});
					selectedCrHtml += '<tr>'+
					'<td>'+result.selectedCourses[i].courseCode+'</td>'+
					'<td><a onclick="showCourseProp(\''+result.selectedCourses[i].courseCode+'\',1)">'+result.selectedCourses[i].courseName+'</a></td>'+
					'<td>'+result.selectedCourses[i].credit+'</td>'+
					'<td>'+result.selectedCourses[i].optimal+'</td>'+
					'<td>'+result.selectedCourses[i].catetory+'</td>'+
					'<td>'+result.selectedCourses[i].classNo+'</td>'+
					'<td><a onclick="showCourseProp(\''+result.selectedCourses[i].courseCode+'\',2)">教学日历</a></td>'+
					((result.sct&&'0'!=result.sct.selectCourseStatus&&1==result.selectedCourses[i].allowSC)?('<td><a onclick="cancelSC(this,2)">'+'删除'+'</a></td>'):((result.sct&&'0'!=result.sct.selectCourseStatus)?'<td></td>':''))+
					'<td>'+result.selectedCourses[i].isEnroll+'</td>'+
					'<td><a onclick="showTeacherInfo(this,2)">'+result.selectedCourses[i].teachName+'</a></td>'+
					'<td style="'+(result.selectedCourses[i].conflict?'color:red;':'')+'">'+useWeekHtml+(result.selectedCourses[i].conflict?'<i class="icon-warning-sign crconflict"></i>':'')+'</td>'+
					'<td style="'+(result.selectedCourses[i].conflict?'color:red;':'')+'">'+classTimeHtml+(result.selectedCourses[i].conflict?'<i class="icon-warning-sign crconflict"></i>':'')+'</td>'+
					'<td>'+roomCodeHtml+'</td>'+
					'</tr>';

					if (result.selectedCourses[i].conflict) {
						showCrConflict = true;
					}
				}
				$('#selectedCoursesTbl tbody').html(selectedCrHtml);

				setTimeout(function () {
					if (showCrConflict) {
						$('#courseConflictFld').css('display', '');
					}
				}, 300);
			} else {
				alert(result.msg);
			}
		},
		error:function(){
			alert('');
		}
	});
}

function cancelSC(aNode, cancelType) {
	if (confirm('课程将被删除，请确认！')) {
		var courseCode = $($(aNode).parents('tr')[0]).find('td:eq(0)').html();
		var classNo;
		if (1 == cancelType) {
			classNo = $($(aNode).parents('tr')[0]).find('td:eq(4)').html();
		} else if (2 == cancelType) {
			classNo = $($(aNode).parents('tr')[0]).find('td:eq(5)').html();
		}
		$.ajax({
			url:contextPath+'/selectcourse/cancelSC',
			type:'POST',
			dataType:'json',
			data:{'courseCode':courseCode, 'classNo':classNo, 'cancelType':cancelType},
			success:function(result){
				if (result.success) {
					alert('删除成功！');
					$('.crDel').remove();
					initCourses();
				} else {
					alert(result.msg);
				}
			},
			error:function(){
				alert('');
			}
		});
	}
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
					debugger
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

function showTeacherInfo(aNode,part) {
	var teachInfo = null;
	if (1 == part) {
		teachInfo = enrollTeacherInfos[$($(aNode).parents('tr')[0]).index()];
	} else if (2 == part) {
		teachInfo = selectedTeacherInfos[$($(aNode).parents('tr')[0]).index()];
	}
	$('#techCol1').html(teachInfo?$.stringDefault(teachInfo['techName'],''):'');
	$('#techCol2').html(teachInfo?$.stringDefault(teachInfo['sex'],''):'');
	$('#techCol3').html(teachInfo?$.stringDefault(teachInfo['technicalTitle'],''):'');
	$('#techCol4').html(teachInfo?$.stringDefault(teachInfo['phone'],''):'');
	$('#techCol5').html(teachInfo?$.stringDefault(teachInfo['office'],''):'');
	$('#techCol6').html(teachInfo?$.stringDefault(teachInfo['email'],''):'');
	$('#techCol7').html(teachInfo?$.stringDefault(teachInfo['homepage'],''):'');
	$('#techCol8').html(teachInfo?$.stringDefault(teachInfo['extend1'],''):'');
	$('#techCol9').html(teachInfo?$.stringDefault(teachInfo['extend2'],''):'');
	$('#techCol10').html(teachInfo?$.stringDefault(teachInfo['extend3'],''):'');
	$('#techCol11').html(teachInfo?$.stringDefault(teachInfo['extend4'],''):'');
	$('#techCol12').html(teachInfo?$.stringDefault(teachInfo['extend5'],''):'');
	$('#teachInfoFld').css('display', '');
}

function closeTechFld() {
	$('#teachInfoFld').css('display', 'none');
}

function showCourseProp(courseCode, type) {
	$.viewCourseMaterial({courseCode:courseCode, type:type, tagId:'onlineView', contextPath:contextPath});
}

function toSCHome() {
	window.location.href = contextPath+'/selectcourse/toSH';
}